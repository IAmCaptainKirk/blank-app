# Purelight Power Dashboards

An internal application for Purelight Power to create custom dashboards.

## Get Started

1. Clone the repository:

```
git clone git@github.com:purelightpower/dashboard-app.git
```

2. Change to the project root directory:

```
cd dashboard-app
```

3. Create a virtual environment. **Important**: You cannot use a version of Python after 3.11 - Snowpark does not support any versions of Python after v3.11. Run `python --version` to check which version you have installed.

```
python -m venv venv
```

4. Activate the virtual environment:

```
source venv/bin/activate
```

5. Install the dependencies:

```
pip install -r requirements.txt
```

6. Add credentials. You must create a `.streamlit/secrets.toml` file that has the following format:

```toml
[snowflake]
account = "SNOWFLAKE_ACCOUNT_IDENTIFIER"
user = "USER_NAME"
password = "USER_PASSWORD"
warehouse = "SNOWFLAKE_WAREHOUSE"
database = "SNOWFLAKE_DATABASE"
schema = "SNOWFLAKE_SCHEMA"
role = "USER_ROLE"
```

7. Once the credentials have been created, you can run the app:

```
python -m streamlit run src/web/streamlit/app.py
```

This should automatically open your default browser. If it doesn't, you can enter the following url in your browser `http://localhost:8501`.

8. When you are done running the development server, you can kill the process by pressing `Ctrl + C` in your terminal where the app was launched.

9. When the server is no longer running, you can deactivate your virtual environment that you activated in step 4 by running the following command:

```
deactivate
```

## Tools

- [Python](https://www.python.org/) - An open source, interpreted programming language. This project is built to run on the [Python 3.11](https://docs.python.org/3.11/) interpreter. One of the core dependencies does not support any Python versions after 3.11.
- [Streamlit](https://streamlit.io/) - An open-source Python framework for data scientists and AI/ML engineers to deliver dynamic data apps with only a few lines of code.
- [Snowpark](https://www.snowflake.com/en/product/features/snowpark/) - An API that provides an intuitive library for querying and processing data at scale in [Snowflake](https://www.snowflake.com/en/).

## Contributors

- [Kirk Bishop](https://github.com/IAmCaptainKirk)
- [Morgan Billingsley](https://github.com/morgbillingsley)