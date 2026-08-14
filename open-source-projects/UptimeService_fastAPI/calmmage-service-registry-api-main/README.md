### How to run the app

Install the required packages:

```bash
pip install -r requirements.txt
```

Install and Start Mongodb following the online documentation.

Run the following command inside the project folder:

```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 5000 --reload
```
