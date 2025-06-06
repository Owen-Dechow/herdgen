# Local Installation

1. Clone Repository

    ```sh
    git clone https://github.com/Owen-Dechow/herdgen.git
    cd /herdgen
    ```

2. Create Environment

    ```
    python3 -m venv venv
    ```

3. Activate Environment

    Unix like system
    ```
    source venv/bin/activate
    ```

    > Some systems may not come with `python-venv`. If so, run `sudo apt-get install
    python3-venv

    Windows
    ```
    venv/Scripts/activate
    ```

    > To exit the environment run `deactivate`.

4. Install Dependencies

    ```
    pip install -r requirements.dev.txt
    ```

5. Create Environment Variables

    ```
    cp herdgen/.env.model herdgen/.env
    ```

6. Setup Database

    ```
    python3 manage.py migrate
    ```

7. Create Superuser
    
    > A super user will give you full access to the django-admin database manager.

    ```
    python3 manage.py createsuperuser
    ```

8. Test

    [Testing.md](./Testing.md)
