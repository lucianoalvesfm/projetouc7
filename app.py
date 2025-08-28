from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from pathlib import Path

# Cria a aplicação Flask
app = Flask(__name__)

# Chave secreta usada para sessões, mensagens flash etc. (aqui uma simples para dev)
app.secret_key = "dev"

# Caminho absoluto do banco de dados (garante que funcione mesmo fora da pasta atual)
DB_PATH = (Path(__file__).parent / "database.db").resolve()


# Função auxiliar para abrir conexão com o banco
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)   # Conecta ao SQLite
    conn.row_factory = sqlite3.Row    # Permite acessar colunas por nome (ex: row["nome"])
    return conn


# Função para criar o banco e tabela caso não existam
def init_db():
    if not DB_PATH.exists():  # Verifica se o arquivo do banco já existe
        print("[INIT_DB] Criando novo banco...")
        with get_db_connection() as conn:  # Abre conexão
            conn.executescript("""        # Executa várias queries de uma vez
                CREATE TABLE produtos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- ID único
                    nome TEXT NOT NULL,                   -- Nome do produto
                    preco INTEGER NOT NULL                   -- Preço em número decimal
                );
            """)
            conn.commit()  # Salva as alterações
        print("[INIT_DB] Banco criado em:", DB_PATH)


# Rota principal ("/") que lista os produtos
@app.route("/pagina", endpoint="home")  # "endpoint" = nome interno da rota
def home():
    with get_db_connection() as conn:  # Abre conexão
        produtos = conn.execute(
            "SELECT id, nome, CAST(preco AS REAL) AS preco FROM produtos ORDER BY id DESC"
        ).fetchall()  # Busca todos os Técnicos, mais recentes primeiro
    return render_template("index.html", produtos=produtos)  # Renderiza a página


# Rota para adicionar um Técnico
@app.route("/add", methods=["GET", "POST"], endpoint="add")
def add_product():
    if request.method == "POST":  # Se o formulário foi enviado
        nome = (request.form.get("nome") or "").strip()  # Pega o nome do form
        preco_raw = (request.form.get("preco") or "").strip()  # Pega o Coren do form

        try:
            if not nome:
                raise ValueError("Nome vazio")  # Não permite Técnico sem nome
            preco = float(preco_raw.replace(",", "."))  # Converte para float (aceita vírgula também)
        except Exception:
            flash("Preencha corretamente nome e coren (ex.: 19.90).", "error")  # Mostra erro
            return redirect(url_for("add"))  # Volta para o formulário

        # Insere no banco
        with get_db_connection() as conn:
            conn.execute("INSERT INTO produtos (nome, preco) VALUES (?, ?)", (nome, preco))
            conn.commit()

        flash("Técnico cadastrado com sucesso!", "success")  # Mensagem de sucesso
        return redirect(url_for("home"))  # Volta para a listagem

    # Se for GET, apenas mostra o formulário
    return render_template("add.html")

# Nova Rota Criada Luciano Alves
@app.route("/", endpoint="pagina")
def pagina():
    return render_template("pagina.html")


# Define a rota para editar Técnicos
# Exemplo: /edit/5 (onde 5 é o ID do Técnico)
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_product(id):
    # Abre conexão com o banco de dados
    conn = get_db_connection()

    # Busca o Técnico pelo ID informado na URL
    produto = conn.execute(
        "SELECT * FROM produtos WHERE id = ?", (id,)
    ).fetchone()

    # Caso o Técnico não exista, retorna mensagem de erro e redireciona para a página inicial
    if not produto:
        flash("Técnico não encontrado!", "error")
        return redirect(url_for("home"))

    # Se o formulário foi enviado (POST), significa que o usuário quer salvar alterações
    if request.method == "POST":
        # Captura os dados enviados no formulário
        nome = request.form["nome"].strip()           # Remove espaços extras do nome
        preco = request.form["preco"].replace(",", ".").strip()  
        # Substitui vírgula por ponto e remove espaços (para aceitar formato brasileiro)

        try:
            # Converte o preço para número decimal (float)
            preco = float(preco)

            # Atualiza o Técnico no banco de dados
            conn.execute(
                "UPDATE produtos SET nome = ?, preco = ? WHERE id = ?",
                (nome, preco, id)
            )
            conn.commit()  # Confirma a alteração no banco

            # Mostra mensagem de sucesso ao usuário
            flash("Técnico atualizado com sucesso!", "success")

        except Exception:
            # Caso ocorra erro (ex: preço inválido), exibe mensagem de erro
            flash("Erro ao atualizar. Verifique os dados.", "error")

        # Fecha conexão com o banco
        conn.close()

        # Redireciona de volta para a lista de Técnicos
        return redirect(url_for("home"))

    # Se for apenas um GET (acesso via link), fecha conexão e exibe formulário preenchido
    conn.close()
    return render_template("edit.html", produto=produto)


@app.route("/delete/<int:id>", methods=["POST", "GET"])
# Define a rota "/delete/<id>", que recebe o ID do Técnico a excluir.
# Aceita tanto GET (mostrar tela de confirmação) quanto POST (executar a exclusão).
def delete_product(id):
    conn = get_db_connection()
    # Abre conexão com o banco de dados

    produto = conn.execute("SELECT * FROM produtos WHERE id = ?", (id,)).fetchone()
    # Busca o Técnico no banco pelo ID informado na URL
    # fetchone() retorna apenas um registro (ou None, se não existir)

    if not produto:
        # Se o Técnico não for encontrado
        flash("Técnico não encontrado!", "error")
        # Mostra uma mensagem de erro
        return redirect(url_for("home"))
        # Redireciona de volta para a página inicial

    if request.method == "POST":
        # Se o usuário confirmar (enviar o formulário com POST)
        conn.execute("DELETE FROM produtos WHERE id = ?", (id,))
        # Executa a exclusão do Técnico pelo ID
        conn.commit()
        # Confirma a operação no banco
        conn.close()
        # Fecha a conexão
        flash("Técnico excluído com sucesso!", "success")
        # Mostra mensagem de sucesso
        return redirect(url_for("home"))
        # Redireciona de volta para a página inicial

    conn.close()
    # Se for uma requisição GET, apenas fecha a conexão

    return render_template("delete.html", produto=produto)
    # Renderiza a página de confirmação de exclusão,
    # passando os dados do Técnico (para mostrar o nome no template)




# Executa o app
if __name__ == "__main__":
    init_db()  # Garante que o banco exista antes de rodar
    app.run(debug=True)  # Executa em modo debug (auto-reload + erros detalhados)
