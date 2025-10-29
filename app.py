import os
import io
import nbformat
from nbclient import NotebookClient
from flask import Flask, render_template, request, send_file, jsonify
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024  # 25MB
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['EXPORT_FOLDER'] = 'exports'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['EXPORT_FOLDER'], exist_ok=True)

def run_notebook_with_params(nb_path: str, params: dict, workdir: str) -> None:
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)
    assignment_lines = []
    for k, v in params.items():
        if isinstance(v, str):
            assignment_lines.append(f'{k} = r"""{v}"""')
        else:
            assignment_lines.append(f"{k} = {repr(v)}")
    param_cell = nbformat.v4.new_code_cell(
        source="# [Injected by app]\n" + "\n".join(assignment_lines)
    )
    nb.cells.insert(0, param_cell)
    client = NotebookClient(
        nb, timeout=120, kernel_name="python3",
        resources={"metadata": {"path": workdir}},
        allow_errors=False, record_timing=False,
    )
    client.execute()

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/download/template/<kind>", methods=["GET"])
def download_template(kind):
    if kind not in ("voetbal", "overig"):
        return "Onbekend template", 404
    fname = "Invulbestand_amateursport_voetbal.xlsx" if kind == "voetbal" else "Invulbestand_amateursport_overig.xlsx"
    path = os.path.join("templates_src", fname)
    return send_file(path, as_attachment=True, download_name=fname)

@app.route("/api/make", methods=["POST"])
def api_make():
    kind = request.form.get("kind", "").strip().lower()
    if kind not in ("voetbal", "overig"):
        return jsonify(ok=False, error="Ongeldig type (voetbal/overig)."), 400
    if "file" not in request.files or request.files["file"].filename == "":
        return jsonify(ok=False, error="Geen bestand ontvangen."), 400

    f = request.files["file"]
    safe = secure_filename(f.filename) or f"upload_{kind}.xlsx"
    up_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{safe}")
    f.save(up_path)

    nb_path = os.path.join("notebooks", "DL_amateursport_voetbal.ipynb" if kind == "voetbal" else "DL_amateursport_overig.ipynb")
    out_name = f"cue_{kind}.txt"
    out_path = os.path.join(app.config['EXPORT_FOLDER'], out_name)

    params = {
        "INPUT_XLSX": os.path.abspath(up_path),
        "OUTPUT_TXT": os.path.abspath(out_path),
        "MODE": kind,
    }
    if os.path.exists(out_path):
        os.remove(out_path)

    try:
        run_notebook_with_params(nb_path, params, workdir=os.getcwd())
    except Exception as e:
        return jsonify(ok=False, error=f"Fout tijdens uitvoeren notebook: {e}"), 500

    if not os.path.exists(out_path):
        return jsonify(ok=False, error="Notebook is uitgevoerd, maar exportbestand werd niet aangetroffen."), 500

    with open(out_path, "r", encoding="utf-8") as fh:
        content = fh.read()
    preview = content if len(content) <= 4000 else (content[:4000] + "\n... (ingekort) ...")

    return jsonify(ok=True, preview=preview, download=f"/download/export/{kind}")

@app.route("/download/export/<kind>", methods=["GET"])
def download_export(kind):
    if kind not in ("voetbal", "overig"):
        return "Onbekend exporttype", 404
    path = os.path.join(app.config['EXPORT_FOLDER'], f"cue_{kind}.txt")
    if not os.path.exists(path):
        return "Geen export aanwezig.", 404
    return send_file(path, as_attachment=True, download_name=f"cue_{kind}.txt", mimetype="text/plain")

@app.route("/health", methods=["GET"])
def health():
    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
