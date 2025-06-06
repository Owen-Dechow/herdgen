# Testing

1. Navigate to Base Dir

    ```
    cd .../herdgen
    ```

    > You should be in the same directory as the `manage.py` file.

2. Run Tests

    ```
    python3 manage.py test --parallel --shuffle
    ```

    > `--parallel`: Run tests asynchronously

    > `--shuffle`: Run tests in random order
