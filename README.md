# TLDR Archives

This repository contains archives of the TLDR newsletter for easy access and better searchability. The goal is to build a conversational layer to chat with and explore tools and important artifacts from this repository in the future.

## Badges

![Daily Archive Pipeline](https://github.com/sivadotblog/tldr/actions/workflows/daily_newsletter.yml/badge.svg)
![Historic Archive Pipeline](https://github.com/sivadotblog/tldr/actions/workflows/backfill_newsletter.yml/badge.svg)

## Installation

To install the necessary dependencies, run the following command:

```bash
pip install -r requirements.txt
```

## Usage

To archive a newsletter, run the following command:

```bash
python .github/actions/tldr_archive/scripts/archive_newsletter.py <category> <date>
```

To backfill newsletters, run the following command:

```bash
python .github/actions/tldr_archive/scripts/backfill_newsletter.py <category> <from_date> <to_date>
```

## Contribution Guidelines

We welcome contributions! Please follow these steps to contribute:

1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Make your changes and commit them with a clear message.
4. Push your changes to your forked repository.
5. Create a pull request to the main repository.

Thank you for your contributions!
