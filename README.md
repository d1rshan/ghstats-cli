# ghstats-cli 

A simple command-line tool to display your GitHub contribution heatmap right in your terminal.

## Installation

### Recommended (via pipx)

The best way to install `ghstats-cli` is using `pipx`, which installs the tool in an isolated environment to avoid dependency conflicts.

1.  **Install pipx (if you don't have it):**

    ```bash
    pip install pipx
    ```

2.  **Install the tool:**

    ```bash
    pipx install ghstats-cli
    ```

### Alternative (via pip)

You can also use standard `pip`. It's recommended to install it in a virtual environment to avoid cluttering your global packages.

```bash
pip install ghstats-cli
````

## Getting Started

### 1\. One-Time Setup

Before you begin, run the interactive setup to configure your default GitHub username and create a Personal Access Token (PAT). The tool will guide you through the process.

```bash
ghstats setup
```

This will securely store your credentials for all future requests.

### 2\. Usage

Once configured, viewing your heatmap is as simple as running the main command.

#### Show Your Own Heatmap

```bash
ghstats
```

#### Show a Specific User's Heatmap

Use the `--user` flag to view the contribution graph of any GitHub user.

```bash
ghstats --user torvalds
```

## All Commands

Here is the full list of available commands and options.

```
Usage: ghstats [OPTIONS] COMMAND [ARGS]...

  ghstats — A sleek tool to show GitHub contribution heatmaps in your
  terminal.

Options:
  --user TEXT  Show heatmap for a specific GitHub user.
  -h, --help   Show this message and exit.

Commands:
  setup        Interactively configure your default username and GitHub token.
  config       Open the configuration file in your default editor.
  show-config  Show current configuration with a masked token.
```

## License

This project is licensed under the MIT License - see the [LICENSE](https://raw.githubusercontent.com/d1rshan/ghstats-cli/refs/heads/main/LICENSE) file for details.
