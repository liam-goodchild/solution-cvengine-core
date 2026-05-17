---
title: Python Helpers for Faster Agent Skills
description: Why I am moving repeatable skill work into Python helpers so Claude and Codex spend fewer tokens on chores.
date: 2026-05-17
slug: python-helpers-for-faster-agent-skills
draft: true
tags:
  - AI
  - Automation
  - DevEx
  - Python
---

I have been changing how my Codex and Claude skills work. The short version: the model should not be doing boring work that a Python script can do faster.

The example I keep coming back to is `git-commit-push`.

That skill used to be the sort of thing where the agent had to inspect the repo, reason about the changed files, decide what to stage, write a commit message, run Git commands, and then explain what happened. Some of that is judgement. A lot of it is plumbing.

So I split the job.

The Python helper now does the mechanical bits:

- reads `git status` in a machine-friendly format
- detects the current branch and upstream
- blocks commits to `main` and `master` unless the repo is explicitly allowed
- scans changed files for obvious risk flags like secrets, `.env` files, binaries, and large files
- stages exactly the files from a JSON plan
- commits with the message from that plan
- pushes to origin
- returns structured output the agent can summarise

The agent still has work to do. It decides whether the risk flags are acceptable. It groups changes into sensible commits when there are enough files to justify it. It writes the commit message in plain English. That is where the model earns its keep.

What I do not need is the model spending half a page thinking about how to run `git status`, whether a relative path escapes the repository, or how to parse a rename from porcelain output. Python is better at that. It is quicker, cheaper, and less likely to hallucinate its way into a weird half-command.

## The token leak is real

This started as a speed thing, but token usage is the bigger irritation.

Claude and Codex are useful enough that I keep giving them more of my workflow. Then I look at the usage and it feels like a pipe with a hole in it. Not a dramatic burst. Just a constant hiss of tokens disappearing into tasks that were never language problems in the first place.

Reading file lists is not a language problem.

Checking whether a branch is protected is not a language problem.

Validating a Terraform variable has a type is not a language problem.

A model can do those things, but making it do them repeatedly is wasteful. It also makes the skill prompt longer because every safety rule has to be explained in prose. Once the rule is in Python, the skill can be smaller: inspect, review, plan, apply.

## Terraform made the same point louder

`format-terraform` pushed me further in this direction.

Terraform formatting has some judgement in it, especially around functional grouping and whether a resource can really be tagged. But most of my standards are objective:

- `.tf` files belong under `infra/`
- `.tfvars` files belong under `infra/vars/`
- variables need descriptions and explicit types
- provider and CLI versions should be pinned
- tfvars files need the exact area header format I use
- secrets should not sit in tfvars
- taggable Azure resources should use `local.tags` or merge with it
- naming should follow the Microsoft Cloud Adoption Framework abbreviations where possible

That is not a prompt. That is a test suite pretending to be a prompt.

So the helper became the test suite. It can scan Terraform files, report findings with rule names, files, lines, severity, and suggested fixes. The model can then explain the findings and decide what is safe to fix. The script supplies the facts. The model supplies judgement.

That boundary matters because Terraform work is exactly where I do not want vibes. I want boring checks. I want repeatable failures. I want the same repository to produce the same findings tomorrow without the model getting creative.

## The shape I like: inspect, plan, apply

The pattern that seems to work is simple.

First, the helper inspects the repo and returns JSON. No drama. Just facts.

Then the model creates a plan. This is where it can decide whether one commit is enough, whether a Terraform fix is safe, or whether a risk flag needs human approval.

Then the helper applies the plan. It should only touch the files named in the plan, and it should fail loudly if something looks wrong.

That shape gives the agent a smaller job and gives me a clearer audit trail. If something breaks, I can usually tell whether the model made a bad judgement or the script made a bad check. Those are different problems, and separating them makes both easier to fix.

## The human bit

I do not want to automate all the thinking out of the workflow. That would be missing the point.

The useful part of these agents is still the squishy bit: explaining trade-offs, naming a commit properly, spotting that two files belong together, or deciding that a Terraform rule needs an exception because Azure is being Azure.

But I do want to stop paying premium-model prices for chores.

So that is the direction I am taking the skills in `ops-developer-config`: small Python wrappers for the predictable work, short skill files that describe the contract, and models used for the parts where language and judgement are actually useful.

It is not glamorous. That is why I like it.
