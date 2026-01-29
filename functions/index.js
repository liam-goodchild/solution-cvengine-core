const { app } = require("@azure/functions");
const { CosmosClient } = require("@azure/cosmos");

const DB = "visitorDatabase";
const CONTAINER = "visitorContainer";
const COUNTER_ID = "visitorCount";

app.http("UpdateVisitorCount", {
  methods: ["GET", "POST"],
  authLevel: "anonymous",
  route: "UpdateVisitorCount",
  handler: async () => {
    try {
      const conn = process.env.CosmosDBConnectionString;

      if (!conn) {
        console.error("Missing CosmosDBConnectionString env var");
        return {
          status: 500,
          headers: { "content-type": "application/json" },
          body: JSON.stringify({
            error: "Server misconfiguration: missing connection string",
          }),
        };
      }

      const client = new CosmosClient(conn);
      const container = client.database(DB).container(CONTAINER);

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

      return {
        status: 200,
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ visitorCount: doc.count }),
      };
    } catch (e) {
      console.error("Failed to update visitor count:", e?.message ?? e);

      return {
        status: 500,
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          error: "Internal server error",
          message: e?.message,
          name: e?.name,
        }),
      };
    }
  },
});
