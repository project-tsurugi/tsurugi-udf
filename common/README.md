# Tsurugi UDF Common Library

## Overview

**tsurugi-udf-common** provides shared utilities and definitions used by both **udf-plugin-builder** and **udf-plugin-viewer**.
It offers consistent interfaces, common helper functions, and protocol definitions for building
and managing User Defined Function (UDF) plugins in Tsurugi Database.

This package is designed to ensure consistent behavior and reduce code duplication
between UDF-related tools.

______________________________________________________________________

## Features

- Common data structures and helper utilities for UDF development
- Shared configuration and constants between plugin tools
- Lightweight dependency for Python-based UDF tools
- Installable via pip

______________________________________________________________________

## Requirements

| Component | Version | Description |
|------------|----------|--------------|
| **Python** | ≥ 3.8 |Required runtime |
| **pip** | ≥ 24.0 |recommended Python package manager |
| **protobuf** | Latest |Protocol Buffers runtime |
| **jinja2** | Latest | Template rendering (if used by utilities) |

## Installation

You can install this package using `pip`:

```bash
pip install .
```

To install it locally for development:

```bash
pip install -e .
```

## License

[Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0)
