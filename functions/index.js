const crypto = require("node:crypto");
const { app } = require("@azure/functions");
const { CosmosClient } = require("@azure/cosmos");

const DB = process.env.CosmosDBDatabaseName || "visitorDatabase";
const CONTAINER = process.env.CosmosDBContainerName || "visitorContainer";
const COUNTER_ID = "visitorCount";
const BREVO_BASE_URL = "https://api.brevo.com/v3";
const DEFAULT_EMAIL_DAILY_LIMIT = 250;
const SUBSCRIBE_RATE_LIMIT_WINDOW_MS = 15 * 60 * 1000;
const SUBSCRIBE_RATE_LIMIT_MAX = 5;
const subscribeAttempts = new Map();

function jsonResponse(status, body) {
  return {
    status,
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  };
}

function getEnv(...names) {
  for (const name of names) {
    if (process.env[name]) {
      return process.env[name];
    }
  }
  return "";
}

function getEmailConfig() {
  const listId = Number.parseInt(getEnv("BREVO_LIST_ID", "BrevoListId"), 10);
  const dailyLimit = Number.parseInt(
    getEnv("EMAIL_DAILY_LIMIT", "EmailDailyLimit") ||
      String(DEFAULT_EMAIL_DAILY_LIMIT),
    10,
  );
  const publicSiteUrl = getEnv("PUBLIC_SITE_URL", "PublicSiteUrl").replace(
    /\/+$/,
    "",
  );

  return {
    apiKey: getEnv("BREVO_API_KEY", "BrevoApiKey"),
    listId,
    notifySecret: getEnv("BLOG_NOTIFY_SECRET", "BlogNotifySecret"),
    dailyLimit: Number.isFinite(dailyLimit)
      ? Math.min(dailyLimit, DEFAULT_EMAIL_DAILY_LIMIT)
      : DEFAULT_EMAIL_DAILY_LIMIT,
    fromEmail: getEnv("EMAIL_FROM", "EmailFrom"),
    fromName: getEnv("EMAIL_FROM_NAME", "EmailFromName") || "Liam Goodchild",
    replyTo: getEnv("EMAIL_REPLY_TO", "EmailReplyTo"),
    publicSiteUrl,
  };
}

function validateBrevoSubscriptionConfig(config) {
  if (!config.apiKey || !Number.isInteger(config.listId) || config.listId <= 0) {
    throw new Error("Missing Brevo subscription configuration");
  }
}

function validateBrevoNotificationConfig(config) {
  validateBrevoSubscriptionConfig(config);

  if (!config.notifySecret || !config.fromEmail || !config.publicSiteUrl) {
    throw new Error("Missing Brevo notification configuration");
  }
}

async function parseJsonBody(request) {
  try {
    return await request.json();
  } catch {
    return {};
  }
}

function normalizeEmail(email) {
  return String(email || "").trim().toLowerCase();
}

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function safeEquals(a, b) {
  const left = Buffer.from(String(a || ""));
  const right = Buffer.from(String(b || ""));

  return left.length === right.length && crypto.timingSafeEqual(left, right);
}

function requestIpHash(request) {
  const forwardedFor = request.headers.get("x-forwarded-for") || "";
  const clientIp = forwardedFor.split(",")[0].trim() || "unknown";

  return crypto.createHash("sha256").update(clientIp).digest("hex");
}

function isSubscribeRateLimited(request) {
  const now = Date.now();
  const key = requestIpHash(request);
  const since = now - SUBSCRIBE_RATE_LIMIT_WINDOW_MS;
  const recentAttempts = (subscribeAttempts.get(key) || []).filter(
    (timestamp) => timestamp > since,
  );

  if (recentAttempts.length >= SUBSCRIBE_RATE_LIMIT_MAX) {
    subscribeAttempts.set(key, recentAttempts);
    return true;
  }

  recentAttempts.push(now);
  subscribeAttempts.set(key, recentAttempts);
  return false;
}

function htmlEscape(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function textFromHtml(value) {
  return String(value ?? "")
    .replace(/<[^>]*>/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

async function brevoRequest(path, options = {}) {
  const config = getEmailConfig();
  validateBrevoSubscriptionConfig(config);

  const response = await fetch(`${BREVO_BASE_URL}${path}`, {
    method: options.method || "GET",
    headers: {
      accept: "application/json",
      "api-key": config.apiKey,
      ...(options.body ? { "content-type": "application/json" } : {}),
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  const raw = await response.text();
  let body = {};
  if (raw) {
    try {
      body = JSON.parse(raw);
    } catch {
      body = { message: raw };
    }
  }

  if (!response.ok) {
    const message =
      body.message ||
      body.error ||
      `Brevo API request failed with ${response.status}`;
    const error = new Error(message);
    error.status = response.status;
    error.body = body;
    throw error;
  }

  return body;
}

function getCosmosContainer() {
  const conn = process.env.CosmosDBConnectionString;

  if (!conn) {
    throw new Error("Missing CosmosDBConnectionString env var");
  }

  const client = new CosmosClient(conn);
  return client.database(DB).container(CONTAINER);
}

async function readNotification(container, slug) {
  const id = `blogNotification:${slug}`;

  try {
    const { resource } = await container.item(id, id).read();
    return resource || null;
  } catch (err) {
    const status = err.code ?? err.statusCode;
    if (status === 404) {
      return null;
    }
    throw err;
  }
}

async function writeNotification(container, slug, details) {
  const now = new Date().toISOString();
  const id = `blogNotification:${slug}`;
  const doc = {
    id,
    type: "blogNotification",
    slug,
    createdAt: now,
    ...details,
  };

  await container.items.upsert(doc);
  return doc;
}

async function getBrevoContactCount(listId) {
  const result = await brevoRequest(
    `/contacts?limit=1&listIds=${encodeURIComponent(String(listId))}`,
  );

  return Number(result.count || 0);
}

function validatePostPayload(payload, config) {
  const slug = String(payload.slug || "").trim();
  const title = String(payload.title || "").trim();
  const description = String(payload.description || "").trim();
  const url = String(payload.url || "").trim();
  const publishedDate = String(payload.publishedDate || payload.date || "").trim();

  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug)) {
    throw new Error("slug must be URL-safe kebab-case");
  }
  if (!title) {
    throw new Error("title is required");
  }
  if (!description) {
    throw new Error("description is required");
  }
  if (!/^\d{4}-\d{2}-\d{2}$/.test(publishedDate)) {
    throw new Error("publishedDate must use YYYY-MM-DD");
  }

  let parsedUrl;
  try {
    parsedUrl = new URL(url);
  } catch {
    throw new Error("url must be an absolute URL");
  }

  if (config.publicSiteUrl) {
    const siteUrl = new URL(config.publicSiteUrl);
    if (parsedUrl.origin !== siteUrl.origin) {
      throw new Error("url must use PUBLIC_SITE_URL origin");
    }
  }

  return {
    slug,
    title,
    description,
    url: parsedUrl.toString(),
    publishedDate,
    commitSha: String(payload.commitSha || "").trim(),
  };
}

function renderBlogNotificationHtml(post, config) {
  const title = htmlEscape(post.title);
  const description = htmlEscape(post.description);
  const url = htmlEscape(post.url);
  const siteUrl = htmlEscape(config.publicSiteUrl);
  const fromName = htmlEscape(config.fromName);

  return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>${title}</title>
  </head>
  <body style="margin:0;padding:0;background:#0f0f12;color:#f5f1e8;font-family:Arial,sans-serif;">
    <div style="display:none;max-height:0;overflow:hidden;">${description}</div>
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#0f0f12;padding:32px 0;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:640px;background:#17171b;border:1px solid #2a2a31;">
            <tr>
              <td style="padding:32px;">
                <p style="margin:0 0 12px;color:#a7a29a;font-size:12px;letter-spacing:2px;text-transform:uppercase;">New blog post</p>
                <h1 style="margin:0 0 18px;color:#f5f1e8;font-size:32px;line-height:1.15;">${title}</h1>
                <p style="margin:0 0 24px;color:#cfc8bd;font-size:16px;line-height:1.6;">${description}</p>
                <p style="margin:0 0 28px;">
                  <a href="${url}" style="display:inline-block;padding:12px 18px;border:1px solid #f05a5a;color:#f5f1e8;text-decoration:none;">Read the post</a>
                </p>
                <p style="margin:0;color:#a7a29a;font-size:13px;line-height:1.5;">
                  You are receiving this because you subscribed on <a href="${siteUrl}" style="color:#f05a5a;">${siteUrl}</a>.
                  <a href="{{ unsubscribe }}" style="color:#f05a5a;">Unsubscribe</a>.
                </p>
                <p style="margin:16px 0 0;color:#a7a29a;font-size:13px;">${fromName}</p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>`;
}

async function createAndSendBrevoCampaign(post, config) {
  const htmlContent = renderBlogNotificationHtml(post, config);
  const campaign = await brevoRequest("/emailCampaigns", {
    method: "POST",
    body: {
      name: `Portfolio blog: ${post.title}`,
      sender: {
        name: config.fromName,
        email: config.fromEmail,
      },
      subject: `New post: ${post.title}`,
      previewText: textFromHtml(post.description).slice(0, 130),
      htmlContent,
      recipients: {
        listIds: [config.listId],
      },
      replyTo: config.replyTo || config.fromEmail,
      tag: "portfolio-blog",
      mirrorActive: false,
    },
  });

  await brevoRequest(`/emailCampaigns/${campaign.id}/sendNow`, {
    method: "POST",
  });

  return campaign;
}

app.http("UpdateVisitorCount", {
  methods: ["GET", "POST"],
  authLevel: "anonymous",
  route: "UpdateVisitorCount",
  handler: async () => {
    try {
      const container = getCosmosContainer();

      let current = 0;

      try {
        const { resource } = await container
          .item(COUNTER_ID, COUNTER_ID)
          .read();
        current = resource?.count ?? 0;
      } catch (err) {
        const status = err.code ?? err.statusCode;
        if (status !== 404) throw err;
        console.log("Counter document not found; will create it.");
      }

      const doc = { id: COUNTER_ID, count: current + 1 };
      await container.items.upsert(doc);

      return jsonResponse(200, { visitorCount: doc.count });
    } catch (e) {
      console.error("Failed to update visitor count:", e?.message ?? e);

      return jsonResponse(500, {
        error: "Internal server error",
        message: e?.message,
        name: e?.name,
      });
    }
  },
});

app.http("Subscribe", {
  methods: ["POST"],
  authLevel: "anonymous",
  route: "Subscribe",
  handler: async (request) => {
    const body = await parseJsonBody(request);
    const email = normalizeEmail(body.email);

    if (body.website) {
      return jsonResponse(200, {
        message: "Thanks — check your inbox when the next post goes live.",
      });
    }

    if (!isValidEmail(email)) {
      return jsonResponse(400, { error: "Please enter a valid email address." });
    }

    if (isSubscribeRateLimited(request)) {
      return jsonResponse(429, {
        error: "Please wait before trying to subscribe again.",
      });
    }

    try {
      const config = getEmailConfig();
      validateBrevoSubscriptionConfig(config);

      await brevoRequest("/contacts", {
        method: "POST",
        body: {
          email,
          listIds: [config.listId],
          updateEnabled: true,
          emailBlacklisted: false,
        },
      });

      return jsonResponse(200, {
        message: "Thanks — you’re on the list for future blog updates.",
      });
    } catch (error) {
      console.error("Failed to subscribe contact:", error?.message ?? error);

      return jsonResponse(503, {
        error: "Subscription service unavailable",
      });
    }
  },
});

app.http("NotifyPost", {
  methods: ["POST"],
  authLevel: "anonymous",
  route: "NotifyPost",
  handler: async (request) => {
    try {
      const config = getEmailConfig();
      validateBrevoNotificationConfig(config);

      const suppliedSecret = request.headers.get("x-notify-secret");
      if (!safeEquals(suppliedSecret, config.notifySecret)) {
        return jsonResponse(401, { error: "Unauthorized" });
      }

      const payload = await parseJsonBody(request);
      const post = validatePostPayload(payload, config);
      const container = getCosmosContainer();
      const existing = await readNotification(container, post.slug);

      if (existing) {
        return jsonResponse(200, {
          status: "skipped",
          reason: "already-notified",
          slug: post.slug,
          notifiedAt: existing.sentAt || existing.createdAt,
        });
      }

      const recipientCount = await getBrevoContactCount(config.listId);

      if (recipientCount > config.dailyLimit) {
        return jsonResponse(409, {
          error: "Brevo free-tier safety limit exceeded",
          recipientCount,
          dailyLimit: config.dailyLimit,
        });
      }

      if (recipientCount === 0) {
        const record = await writeNotification(container, post.slug, {
          status: "skipped-no-subscribers",
          recipientCount,
          sentAt: new Date().toISOString(),
          post,
        });

        return jsonResponse(200, {
          status: record.status,
          slug: post.slug,
          recipientCount,
        });
      }

      const campaign = await createAndSendBrevoCampaign(post, config);
      const record = await writeNotification(container, post.slug, {
        status: "sent",
        recipientCount,
        brevoCampaignId: campaign.id,
        sentAt: new Date().toISOString(),
        post,
      });

      return jsonResponse(200, {
        status: record.status,
        slug: post.slug,
        recipientCount,
        brevoCampaignId: campaign.id,
      });
    } catch (error) {
      console.error("Failed to notify blog subscribers:", error?.message ?? error);

      const status = error.message?.startsWith("Missing") ? 503 : 400;
      return jsonResponse(status, {
        error: "Blog notification failed",
        message: error?.message,
      });
    }
  },
});
