# Testing Guide

This project uses **`pytest`** to run a suite of automated tests that ensure code quality, prevent regressions, and validate functionality against real-world platforms.

---

## Setup for Testing

Before running tests, you must set up your environment correctly.

1. **Activate Your Virtual Environment**

    ```bash
    source venv/bin/activate
    ```

2. **Install the Project in Editable Mode**
    This crucial step makes your project's source code visible to `pytest`.

    ```bash
    pip install -e .
    ```

---

## Running Tests

All commands should be run from the root directory of the project.

### Basic Commands

* **Run All Tests**
    This command discovers and runs every test in the `/tests` directory.

    ```bash
    pytest
    ```

* **Run with Verbose Output**
    For a more detailed view of which tests are running and their status, use the `-v` (verbose) and `-s` (show `print` statements) flags.

    ```bash
    pytest -v -s
    ```

### Filtering Tests

Our tests are marked to give you fine-grained control over what you run. The current tests are marked as `e2e` (end-to-end).

* **Run Only End-to-End Tests**
    This is useful for running only the slow, network-dependent tests.

    ```bash
    pytest -m e2e
    ```

* **Exclude End-to-End Tests**
    Run all tests *except* the slow `e2e` tests. This is great for quick, local checks.

    ```bash
    pytest -m "not e2e"
    ```

* **Run Tests by Keyword**
    Use the `-k` flag to run tests whose names match a specific expression.

    ```bash
    # Runs only the test_youtube_playlist function
    pytest -k "test_youtube_playlist"

    # Runs all tests related to YouTube
    pytest -k "youtube"
    ```

* **Run a Specific File**

    ```bash
    pytest tests/test_end_to_end.py
    ```

### Debugging

* **Stop on First Failure**
    Use the `-x` flag to stop the test session immediately after the first test fails. This is helpful for focused debugging.

    ```bash
    pytest -x
    ```

---

## Test Structure

* `/tests`: All test files are located here.
* `tests/conftest.py`: This special file contains **fixtures**, which are helper functions that handle setup and cleanup. Our `temp_output_dir` fixture automatically creates and removes the temporary folders used during testing.
* `tests/test_end_to_end.py`: Contains tests that interact with live platform APIs to validate the full application pipeline.
