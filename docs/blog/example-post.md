---
title: "Example Blog Post Title"
description: "A short one-line summary of what this post is about."
date: "2026-04-24"
readTime: "4 min"
tags:
  - Azure
  - DevOps
  - Terraform
slug: "example-post"
---

A short opening paragraph that introduces the topic and explains why it matters.

## The Problem

Describe the problem, context, or situation.

> We needed a repeatable way to deploy Azure infrastructure without relying on manual portal changes.

## The Approach

Explain the solution at a high level.

- Use Infrastructure as Code
- Keep environments consistent
- Validate changes before deployment
- Automate security checks where possible

## Example

```bash
terraform fmt -check
terraform validate
terraform plan
```

You can also include code blocks for Bicep, YAML, PowerShell, or Terraform:

```hcl
resource "azurerm_resource_group" "example" {
  name     = "rg-example-uksouth"
  location = "uksouth"
}
```

## What I Learned

1. Keep the workflow simple.
2. Automate the boring checks.
3. Make failure obvious and early.

## Final Thoughts

Close with a short conclusion or recommendation.
