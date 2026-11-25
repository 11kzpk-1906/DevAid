# Analyzer Plugins

Plugins are discovered through the Python `devaid.analyzers` entry-point group. New plugins should include a `devaid-plugin.toml` manifest with:

```toml
[devaid-plugin]
name = "example"
api-version = 1
entry-point = "example.plugin:analyze"
```

The callback accepts one `pathlib.Path`. The SDK provides immutable `AnalyzerFinding` and `AnalyzerResult` types. Listing plugins does not import plugin code; running a selected plugin does.
