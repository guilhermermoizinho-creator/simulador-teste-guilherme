from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__)

# =========================
# BASE TEMPORÁRIA EM MEMÓRIA
# =========================
ccts = {
    "CCT Limpeza SP": {
        "funcoes": [
            {"funcao": "Auxiliar de Limpeza", "piso": 1650.00, "vigencia": "2026-01-01"},
            {"funcao": "Limpador de Vidro", "piso": 1800.00, "vigencia": "2026-01-01"},
        ],
        "beneficios": [
            {"nome": "Vale Transporte", "valor": 300.00, "desconto": 120.00},
            {"nome": "Vale Refeição", "valor": 500.00, "desconto": 50.00},
        ]
    },
    "CCT Portaria SP": {
        "funcoes": [
            {"funcao": "Porteiro", "piso": 1850.00, "vigencia": "2026-01-01"},
            {"funcao": "Controlador de Acesso", "piso": 1900.00, "vigencia": "2026-01-01"},
        ],
        "beneficios": [
            {"nome": "Vale Transporte", "valor": 280.00, "desconto": 100.00},
            {"nome": "Cesta Básica", "valor": 200.00, "desconto": 0.00},
        ]
    },
    "CCT Recepção SP": {
        "funcoes": [
            {"funcao": "Recepcionista", "piso": 2100.00, "vigencia": "2026-01-01"},
        ],
        "beneficios": [
            {"nome": "Vale Transporte", "valor": 250.00, "desconto": 90.00},
        ]
    }
}

propostas = [
    {
        "id": 1,
        "nome": "0442026 - Einstein",
        "cliente": "Einstein",
        "local": "São Paulo",
        "unidade": "Morumbi",
        "revisao": "R00",
        "planejador": "Guilherme",
        "status": "Ativa",
        "cct": "CCT Limpeza SP",
        "beneficios": [
            {"nome": "Vale Transporte", "valor": 300.00, "desconto": 120.00},
            {"nome": "Vale Refeição", "valor": 500.00, "desconto": 50.00},
        ],
        "linhas": [
            {
                "qtd": 2,
                "funcao": "Auxiliar de Limpeza",
                "obs": "",
                "setor": "Limpeza",
                "inicio": "08:00",
                "fim": "17:00",
                "salario_base": 1650.00,
                "beneficio_unitario": 800.00,
                "desconto_unitario": 170.00,
                "salario_liquido_unitario": 1480.00,
                "total_salario_base": 3300.00,
                "total_beneficios": 1600.00,
                "total_descontos": 340.00,
                "total_liquido": 2960.00,
            }
        ],
        "resumo": {
            "total_postos": 1,
            "total_funcionarios": 2,
            "total_salario_base": 3300.00,
            "total_beneficios": 1600.00,
            "total_descontos": 340.00,
            "total_liquido": 2960.00,
        }
    }
]


# =========================
# FUNÇÕES AUXILIARES
# =========================
def gerar_id_proposta():
    if not propostas:
        return 1
    return max(p["id"] for p in propostas) + 1


def to_float(valor):
    try:
        return float(str(valor).replace(",", "."))
    except (ValueError, TypeError):
        return 0.0


def to_int(valor):
    try:
        return int(valor)
    except (ValueError, TypeError):
        return 0


def buscar_proposta_por_id(proposta_id):
    return next((p for p in propostas if p["id"] == proposta_id), None)


def calcular_linhas_e_resumo(nome_cct, dados_form):
    qtds = dados_form.getlist("qtd[]")
    funcoes = dados_form.getlist("funcao[]")
    obs_list = dados_form.getlist("obs[]")
    setores = dados_form.getlist("setor[]")
    inicios = dados_form.getlist("inicio[]")
    fins = dados_form.getlist("fim[]")
    salarios = dados_form.getlist("salario_base[]")

    beneficios_cct = ccts.get(nome_cct, {}).get("beneficios", [])
    beneficio_unitario = sum(to_float(b["valor"]) for b in beneficios_cct)
    desconto_unitario = sum(to_float(b["desconto"]) for b in beneficios_cct)

    linhas = []
    total_funcionarios = 0
    total_salario_base = 0.0
    total_beneficios = 0.0
    total_descontos = 0.0
    total_liquido = 0.0

    for i in range(len(funcoes)):
        qtd = to_int(qtds[i]) if i < len(qtds) else 0
        funcao = funcoes[i].strip() if i < len(funcoes) else ""
        obs = obs_list[i].strip() if i < len(obs_list) else ""
        setor = setores[i].strip() if i < len(setores) else ""
        inicio = inicios[i].strip() if i < len(inicios) else ""
        fim = fins[i].strip() if i < len(fins) else ""
        salario_base = to_float(salarios[i]) if i < len(salarios) else 0.0

        if not (qtd or funcao or setor or inicio or fim):
            continue

        salario_liquido_unitario = salario_base - desconto_unitario
        total_salario_base_linha = qtd * salario_base
        total_beneficios_linha = qtd * beneficio_unitario
        total_descontos_linha = qtd * desconto_unitario
        total_liquido_linha = qtd * salario_liquido_unitario

        linha = {
            "qtd": qtd,
            "funcao": funcao,
            "obs": obs,
            "setor": setor,
            "inicio": inicio,
            "fim": fim,
            "salario_base": salario_base,
            "beneficio_unitario": beneficio_unitario,
            "desconto_unitario": desconto_unitario,
            "salario_liquido_unitario": salario_liquido_unitario,
            "total_salario_base": total_salario_base_linha,
            "total_beneficios": total_beneficios_linha,
            "total_descontos": total_descontos_linha,
            "total_liquido": total_liquido_linha,
        }
        linhas.append(linha)

        total_funcionarios += qtd
        total_salario_base += total_salario_base_linha
        total_beneficios += total_beneficios_linha
        total_descontos += total_descontos_linha
        total_liquido += total_liquido_linha

    resumo = {
        "total_postos": len(linhas),
        "total_funcionarios": total_funcionarios,
        "total_salario_base": total_salario_base,
        "total_beneficios": total_beneficios,
        "total_descontos": total_descontos,
        "total_liquido": total_liquido,
    }

    return linhas, resumo


def montar_nome_proposta(cliente, unidade):
    cliente = (cliente or "").strip()
    unidade = (unidade or "").strip()

    if cliente and unidade:
        return f"{cliente} - {unidade}"
    if cliente:
        return cliente
    if unidade:
        return unidade
    return "Nova Proposta"


# =========================
# ROTAS
# =========================
@app.route("/")
def index():
    return render_template("index.html", propostas=propostas)


@app.route("/cct", methods=["GET", "POST"])
def cct():
    global ccts

    if request.method == "POST":
        nome_cct = request.form.get("nome_cct", "").strip()

        funcoes = request.form.getlist("funcao[]")
        pisos = request.form.getlist("piso[]")
        vigencias = request.form.getlist("vigencia[]")

        beneficios_nomes = request.form.getlist("beneficio_nome[]")
        beneficios_valores = request.form.getlist("beneficio_valor[]")
        beneficios_descontos = request.form.getlist("beneficio_desconto[]")

        if nome_cct:
            if nome_cct not in ccts:
                ccts[nome_cct] = {"funcoes": [], "beneficios": []}

            # Adiciona funções
            for i in range(len(funcoes)):
                funcao = funcoes[i].strip()
                piso = pisos[i].strip() if i < len(pisos) else ""
                vigencia = vigencias[i].strip() if i < len(vigencias) else ""

                if funcao and piso and vigencia:
                    ccts[nome_cct]["funcoes"].append({
                        "funcao": funcao,
                        "piso": to_float(piso),
                        "vigencia": vigencia
                    })

            # Adiciona benefícios
            for i in range(len(beneficios_nomes)):
                nome = beneficios_nomes[i].strip()
                valor = beneficios_valores[i].strip() if i < len(beneficios_valores) else ""
                desconto = beneficios_descontos[i].strip() if i < len(beneficios_descontos) else ""

                if nome and valor:
                    ccts[nome_cct]["beneficios"].append({
                        "nome": nome,
                        "valor": to_float(valor),
                        "desconto": to_float(desconto)
                    })

        return redirect(url_for("cct"))

    return render_template("cct.html", ccts=ccts)


@app.route("/proposta", methods=["GET", "POST"])
def nova_proposta():
    if request.method == "POST":
        cliente = request.form.get("cliente", "").strip()
        local = request.form.get("local", "").strip()
        unidade = request.form.get("unidade", "").strip()
        revisao = request.form.get("revisao", "").strip()
        planejador = request.form.get("planejador", "").strip()
        status = request.form.get("status", "").strip()
        nome_cct = request.form.get("nome_cct", "").strip()

        linhas, resumo = calcular_linhas_e_resumo(nome_cct, request.form)
        beneficios = ccts.get(nome_cct, {}).get("beneficios", [])

        propostas.append({
            "id": gerar_id_proposta(),
            "nome": montar_nome_proposta(cliente, unidade),
            "cliente": cliente,
            "local": local,
            "unidade": unidade,
            "revisao": revisao,
            "planejador": planejador,
            "status": status or "Rascunho",
            "cct": nome_cct,
            "beneficios": beneficios,
            "linhas": linhas,
            "resumo": resumo
        })

        return redirect(url_for("index"))

    return render_template(
        "proposta_form.html",
        ccts=ccts,
        proposta=None,
        modo="nova"
    )


@app.route("/proposta/<int:proposta_id>")
def visualizar_proposta(proposta_id):
    proposta = buscar_proposta_por_id(proposta_id)
    if not proposta:
        return "Proposta não encontrada", 404

    return render_template("proposta_detalhe.html", proposta=proposta)


@app.route("/proposta/<int:proposta_id>/editar", methods=["GET", "POST"])
def editar_proposta(proposta_id):
    proposta = buscar_proposta_por_id(proposta_id)
    if not proposta:
        return "Proposta não encontrada", 404

    if request.method == "POST":
        cliente = request.form.get("cliente", "").strip()
        local = request.form.get("local", "").strip()
        unidade = request.form.get("unidade", "").strip()
        revisao = request.form.get("revisao", "").strip()
        planejador = request.form.get("planejador", "").strip()
        status = request.form.get("status", "").strip()
        nome_cct = request.form.get("nome_cct", "").strip()

        linhas, resumo = calcular_linhas_e_resumo(nome_cct, request.form)
        beneficios = ccts.get(nome_cct, {}).get("beneficios", [])

        proposta["nome"] = montar_nome_proposta(cliente, unidade)
        proposta["cliente"] = cliente
        proposta["local"] = local
        proposta["unidade"] = unidade
        proposta["revisao"] = revisao
        proposta["planejador"] = planejador
        proposta["status"] = status or "Rascunho"
        proposta["cct"] = nome_cct
        proposta["beneficios"] = beneficios
        proposta["linhas"] = linhas
        proposta["resumo"] = resumo

        return redirect(url_for("visualizar_proposta", proposta_id=proposta_id))

    return render_template(
        "proposta_form.html",
        ccts=ccts,
        proposta=proposta,
        modo="editar"
    )


@app.route("/proposta/<int:proposta_id>/excluir", methods=["POST"])
def excluir_proposta(proposta_id):
    global propostas
    propostas = [p for p in propostas if p["id"] != proposta_id]
    return redirect(url_for("index"))


@app.route("/buscar-dados-cct/<nome_cct>", methods=["GET"])
def buscar_dados_cct(nome_cct):
    dados = ccts.get(nome_cct, {"funcoes": [], "beneficios": []})
    return jsonify(dados)


if __name__ == "__main__":
    app.run(debug=True)