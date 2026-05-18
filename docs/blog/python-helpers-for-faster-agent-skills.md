---
title: Python Helpers for Faster Agent Skills
description: What I learned while moving repeatable work in ops-developer-config into Python-backed Codex and Claude skills.
date: 2026-05-17
slug: python-helpers-for-faster-agent-skills
draft: false
tags:
  - AI
  - Automation
  - DevEx
  - Python
---

I have been reworking the skills in my [`ops-developer-config`](https://github.com/liam-goodchild/ops-developer-config) repository so Codex and Claude spend less time doing chores.

That repo is where I keep the small workflows I use across projects: Git cleanup, commit and push, PR creation, Terraform formatting, Obsidian maintenance, study helpers, blog post creation, and a few others. The pattern that has emerged is simple: if the task is repeatable, deterministic, and easy to express as inputs and outputs, it probably belongs in Python. The model should handle judgement, not parse command output for the hundredth time.

The clearest example is `git-commit-push`.

The old version asked the agent to inspect the repository, understand the changed files, decide what to stage, write a commit message, run Git, and explain the result. Some of that is useful model work. Most of it is plumbing.

So I moved the plumbing into `skills/git/git-commit-push/scripts/git-commit-push-helper.py`.

The helper now does the mechanical work:

- reads `git status` in a machine-friendly format
- detects the current branch and upstream
- blocks commits to `main` and `master` unless the repo is explicitly allowed
- flags likely secrets, `.env` files, binaries, and large files
- stages exactly the files named in a JSON plan
- commits with the supplied message
- pushes to origin
- returns structured output for the agent to summarise

The skill file is much thinner now. It tells the agent to run `inspect`, review fields like `has_changes`, `blocked`, and `risk_flags`, create a plan JSON outside the repo, and then call `apply`. That is a better contract than a long prompt full of shell instructions.

The model still earns its keep. It decides whether a warning is acceptable, whether the changed files should be split into more than one commit, and what the commit message should say. But it no longer has to remember exactly how I want Git called, or how to avoid staging the plan file it just created.

## The token leak was hiding in plain sight

This started as a speed improvement, but token usage became the real reason to keep going.

I use these agents often enough that small inefficiencies add up. A model reading the same file lists, restating the same safety checks, and walking through the same command sequence is not doing high-value work. It is just spending tokens on process.

A few examples from the repo made this obvious:

- `git-cleanup` can inspect branches and tags, produce a deletion plan, dry-run it, and apply it without the model hand-rolling Git commands.
- `create-blog-post` can handle slug generation, front matter checks, and generated frontend validation.
- `format-markdown` can do deterministic Markdown cleanup while leaving tone and meaning to the model.
- `humanizer` can flag repeated AI-writing patterns so the model has a better starting point for editing.

None of those checks are language problems. They are small, boring programs. Once they are Python helpers, the skill prompts get shorter and the agent has fewer chances to improvise something unsafe.

## Terraform made the boundary obvious

The `format-terraform` skill pushed this from a preference into a rule.

Terraform work is not where I want creative interpretation. I want repeatable checks and clear failures. The helper in `skills/terraform/format-terraform/scripts/format-terraform-helper.py` looks for the standards I use across my infrastructure repositories:

- `.tf` files under `infra/`
- `.tfvars` files under `infra/vars/`
- variables with descriptions and explicit types
- pinned Terraform and provider versions
- committed lock files
- exact area header formatting in tfvars files
- no secrets in tfvars
- taggable Azure resources using `local.tags` or `merge(local.tags, ...)`
- naming that follows Microsoft Cloud Adoption Framework abbreviations where it fits

Those rules should not live only as prose in a prompt. The helper can report findings with rule names, paths, line numbers, severity, and suggested fixes. The model can then explain the findings, decide what is safe to change, and spot the cases that need human judgement: provider quirks, CAF exceptions, externally supplied variables, or Azure resources that do not behave quite like the docs imply.

That split matters. If `format-terraform` produces a bad result, I can tell whether the helper enforced the wrong rule or the model made a poor judgement call. Before this change, those two failure modes were mixed together.

## The shape that keeps working

Most of the Python-backed skills in `ops-developer-config` are settling into the same flow:

1. `inspect` gathers facts and returns compact JSON.
2. The agent reviews the JSON and creates an explicit plan.
3. `apply` performs the side effects from that plan.

For risky operations, I add a dry-run or a blocking field. For file writes, I make the helper validate repository-relative paths. For multi-step changes, the plan lives outside the repository so the agent does not accidentally commit its own scratch file.

It is not a complicated architecture, but it makes the skills easier to trust. The Python code owns parsing, validation, command orchestration, and stable output. The model owns the parts that actually benefit from language: explanation, grouping, summaries, trade-offs, and the occasional judgement call.

## What I learned

The main finding from this work is that better agent skills are often smaller agent skills.

My first instinct was to make the prompts more detailed: add more rules, more examples, more warnings. That works up to a point, but it also makes every run heavier. Moving objective checks into helper scripts has been cleaner. The prompt becomes a contract. The helper becomes the testable part. The model gets a narrower job.

That is the direction I am taking `ops-developer-config`: short skill files, Python helpers for the predictable work, and agents reserved for the parts where judgement matters.

It is not glamorous. That is why I like it.
