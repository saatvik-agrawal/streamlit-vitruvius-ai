**Credits**: Nethan Mikil Kuruppu (@atomikk65535)

## How to use this quickly?

Check out https://huggingface.co/spaces/atomikk/PID

## 🚀 How to build this?

1. Clone the repository or open it in a GitHub Codespace.
2. Open the root folder in a terminal.
3. Run:
   ```bash
   streamlit run app.py
   ```


---

## 📦 Requirements

Install these Python packages and libraries before running the app:

- `pyyaml` – for reading `.yaml` config files  
  ```bash
  pip install pyyaml
  ```

- `python-dotenv` – for loading environment variables from `.env`  
  ```bash
  pip install python-dotenv
  ```

- `streamlit` – for running the web app  
  ```bash
  pip install streamlit
  ```

Install all at once:
```bash
pip install pyyaml python-dotenv streamlit
```

---

## 📂 File Structure

```
project-root/
├── app.py
├── config.yaml
├── .env
├── README.md
```

---

## ℹ️ Notes

- `.env`: use `KEY=VALUE` format
- `.yaml`: follow standard YAML syntax
