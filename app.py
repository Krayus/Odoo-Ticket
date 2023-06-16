#!/usr/bin/env python3

from flask import Flask, url_for, request, render_template
import requests
import urllib.request, json
import pandas as pd
from saml import uddsaml
import records, yaml, os

app = Flask(__name__)
app.debug = True
app.secret_key = 'Ru@y5beid9eishae?y"oo/boopho/eMeewa1ne6eeCothingae<ne)r4So0aeDe2'
app.dbprod = 'mssql+pymssql://uddusers:Udd2k20!@dbprod.udd.net/DB_CTRLMAILS'
app.config["TEMPLATES_AUTO_RELOAD"] = True

sp = uddsaml.UDDServiceProvider(app)

@app.before_request   
def before_request_callback():
    # whitelisted urls, paths where we don't require user authentication.
    # app.config['SP_PASE_PATH'] path MUST be in this whitelist.
    whitelist = [
        app.config['SP_PASE_PATH']
    ]
    for x in whitelist:
        if request.path.startswith(x):
            return

    app.config['_SP_UNAUTH_URL'] = request.path
    sp.login_required()


@app.route('/')
def private():
    auth_data = sp.get_auth_data_in_session()
    message = f'''
    <p>You are logged in as <strong>{auth_data.nameid}</strong>.
    The IdP sent back the following attributes:<p>
    '''

    attrs = '<dl>{}</dl>'.format(''.join(
        f'<dt>{attr}</dt><dd>{value}</dd>'
        for attr, value in auth_data.attributes.items()))

    logout_url = url_for('flask_saml2_sp.logout')
    logout = f'<form action="{logout_url}" method="POST"><input type="submit" value="Log out"></form>'

    #return message + attrs + logout
    if 'UDD_Tipo_Usuario' in auth_data.attributes:
        if auth_data.attributes['UDD_Tipo_Usuario'] == 'Funcionario':
            return render_template('index.html', attrs=auth_data.attributes)
            
    #return render_template('noauthorized.html')

@app.route('/tipo_solicitud')
def tipo_solicitud():
    auth_data = sp.get_auth_data_in_session()
    tipo_solicitud = request.args.get('tipo_solicitud')
    if tipo_solicitud == 'listas':
        return render_template('listas.html')
    if tipo_solicitud == 'acceso':
        return render_template('listas.html')
    elif tipo_solicitud == 'none':
        return ''
    return 'Pending...'

@app.route('/secciones', methods = ['POST', 'GET'])
def secciones():
    matricula = config['matricula']
        
    if request.method == 'POST':
        label = request.form.get('label', 'option')
        carrera = request.form.get('carrera', None)
        sede = request.form.get('sede', None)
        curso = request.form.get('curso', None)
        anhio = request.form.get('anhio', 0)
        periodo = request.form.get('periodo', 0)
    else:
        label = request.args.get('label', 'option')
        carrera = request.args.get('carrera', None)
        sede = request.args.get('sede', None)
        curso = request.args.get('curso', None)
        anhio = request.args.get('anhio', 0)
        periodo = request.args.get('periodo', 0)
    
    db_matricula = records.Database(matricula)
    if carrera and sede:
        rs = db_matricula.query("""
            SELECT S.CODSECC, S.CODSEDE, S.CODCARR, S.ANO,S.PERIODO, S.BIMESTRE, S.CODRAMO,R.NOMBRE AS 'NOMBRE_RAMO'
            FROM RA_SECCIO S
                INNER JOIN RA_RAMO R
            ON S.CODRAMO = R.CODRAMO
            WHERE S.ANO = {anhio} AND S.PERIODO = {periodo} AND S.CODESTADO = 3 AND S.CODSEDE = '{sede}' AND S.CODCARR = '{codcarr}'
            AND R.CODRAMO = '{codramo}'
            ORDER BY 1,2,3        
        """.format(sede=sede, codcarr=carrera, codramo=curso, anhio=anhio, periodo=periodo), fetchall=True)
    elif carrera and not sede:
        rs = db_matricula.query("""
            SELECT S.CODSECC, S.CODSEDE, S.CODCARR, S.ANO,S.PERIODO, S.BIMESTRE, S.CODRAMO,R.NOMBRE AS 'NOMBRE_RAMO'
            FROM RA_SECCIO S
                INNER JOIN RA_RAMO R
            ON S.CODRAMO = R.CODRAMO
            WHERE S.ANO = {anhio} AND S.PERIODO = {periodo} AND S.CODESTADO = 3 AND S.CODCARR = '{codcarr}'
            AND R.CODRAMO = '{codramo}'
            ORDER BY 1,2,3        
        """.format(sede=sede, codcarr=carrera, codramo=curso, anhio=anhio, periodo=periodo), fetchall=True)
    elif not carrera and sede:
        rs = db_matricula.query("""
            SELECT S.CODSECC, S.CODSEDE, S.CODCARR, S.ANO,S.PERIODO, S.BIMESTRE, S.CODRAMO,R.NOMBRE AS 'NOMBRE_RAMO'
            FROM RA_SECCIO S
                INNER JOIN RA_RAMO R
            ON S.CODRAMO = R.CODRAMO
            WHERE S.ANO = {anhio} AND S.PERIODO = {periodo} AND S.CODESTADO = 3 AND S.CODSEDE = '{sede}'
            AND R.CODRAMO = '{codramo}'
            ORDER BY 1,2,3        
        """.format(sede=sede, codcarr=carrera, codramo=curso, anhio=anhio, periodo=periodo), fetchall=True)
    else:
        rs = db_matricula.query("""
            SELECT S.CODSECC, S.CODSEDE, S.CODCARR, S.ANO,S.PERIODO, S.BIMESTRE, S.CODRAMO,R.NOMBRE AS 'NOMBRE_RAMO'
            FROM RA_SECCIO S
                INNER JOIN RA_RAMO R
            ON S.CODRAMO = R.CODRAMO
            WHERE S.ANO = {anhio} AND S.PERIODO = {periodo} AND S.CODESTADO = 3
            AND R.CODRAMO = '{codramo}'
            ORDER BY 1,2,3        
        """.format(sede=sede, codcarr=carrera, codramo=curso, anhio=anhio, periodo=periodo), fetchall=True)
        
    if 'html' in request.headers.get('Accept'):
        return render_template('secciones.html', secciones=rs.as_dict(), label=label)
    elif 'json' in request.headers.get('Accept'):
        return render_template('secciones.json', secciones=rs)
    return ''
    
@app.route('/cursos', methods = ['POST', 'GET'])
def cursos():
    matricula = config['matricula']
        
    if request.method == 'POST':
        label = request.form.get('label', 'option')
        carrera = request.form.get('carrera', None)
        sede = request.form.get('sede', None)
        anhio = request.form.get('anhio', 0)
        periodo = request.form.get('periodo', 0)
    else:
        label = request.args.get('label', 'option')
        carrera = request.args.get('carrera', None)
        sede = request.args.get('sede', None)
        anhio = request.args.get('anhio', 0)
        periodo = request.args.get('periodo', 0)
    
    db_matricula = records.Database(matricula)
    if carrera and sede:
        rs = db_matricula.query("""
            SELECT DISTINCT S.CODSEDE, S.CODCARR, S.ANO,S.PERIODO, S.BIMESTRE, S.CODRAMO,R.NOMBRE AS 'NOMBRE_RAMO'
            FROM RA_SECCIO S
                INNER JOIN RA_RAMO R
            ON S.CODRAMO = R.CODRAMO
            WHERE S.ANO = {anhio} AND S.PERIODO = {periodo} AND S.CODESTADO = 3 AND S.CODSEDE = '{sede}' AND S.CODCARR = '{codcarr}'
            ORDER BY 1,2,3        
        """.format(sede=sede, codcarr=carrera, anhio=anhio, periodo=periodo), fetchall=True)
    elif carrera and not sede:
        rs = db_matricula.query("""
            SELECT DISTINCT S.CODSEDE, S.CODCARR, S.ANO,S.PERIODO, S.BIMESTRE, S.CODRAMO,R.NOMBRE AS 'NOMBRE_RAMO'
            FROM RA_SECCIO S
                INNER JOIN RA_RAMO R
            ON S.CODRAMO = R.CODRAMO
            WHERE S.ANO = {anhio} AND S.PERIODO = {periodo} AND S.CODESTADO = 3 AND S.CODCARR = '{codcarr}'
            ORDER BY 1,2,3        
        """.format(sede=sede, codcarr=carrera, anhio=anhio, periodo=periodo), fetchall=True)
    elif not carrera and sede:
        rs = db_matricula.query("""
            SELECT DISTINCT S.CODSEDE, S.CODCARR, S.ANO,S.PERIODO, S.BIMESTRE, S.CODRAMO,R.NOMBRE AS 'NOMBRE_RAMO'
            FROM RA_SECCIO S
                INNER JOIN RA_RAMO R
            ON S.CODRAMO = R.CODRAMO
            WHERE S.ANO = {anhio} AND S.PERIODO = {periodo} AND S.CODESTADO = 3 AND S.CODSEDE = '{sede}'
            ORDER BY 1,2,3        
        """.format(sede=sede, codcarr=carrera, anhio=anhio, periodo=periodo), fetchall=True)
    else:
        rs = db_matricula.query("""
            SELECT DISTINCT S.CODSEDE, S.CODCARR, S.ANO,S.PERIODO, S.BIMESTRE, S.CODRAMO,R.NOMBRE AS 'NOMBRE_RAMO'
            FROM RA_SECCIO S
                INNER JOIN RA_RAMO R
            ON S.CODRAMO = R.CODRAMO
            WHERE S.ANO = {anhio} AND S.PERIODO = {periodo} AND S.CODESTADO = 3
            ORDER BY 1,2,3        
        """.format(sede=sede, codcarr=carrera, anhio=anhio, periodo=periodo), fetchall=True)
        
    if 'html' in request.headers.get('Accept'):
        return render_template('cursos.html', cursos=rs.as_dict(), label=label)
    elif 'json' in request.headers.get('Accept'):
        return render_template('cursos.json', cursos=rs)
    return ''

@app.route('/carreras', methods = ['POST', 'GET'])
def carreras():
    matricula = config['matricula']
        
    if request.method == 'POST':
        label = request.form.get('label', 'option')
        sede = request.form.get('sede', None)
    else:
        label = request.args.get('label', 'option')
        sede = request.args.get('sede', None)
    
    db_matricula = records.Database(matricula)
    if sede:
        rs = db_matricula.query("SELECT * FROM MT_CARRER WHERE sede = '{sede}' AND TIPOCARR=1".format(sede=sede), fetchall=True)
    else:
        rs = db_matricula.query('SELECT * FROM MT_CARRER WHERE TIPOCARR=1', fetchall=True)
        
    if 'html' in request.headers.get('Accept'):
        return render_template('carreras.html', carreras=rs.as_dict(), label=label)
    elif 'json' in request.headers.get('Accept'):
        return render_template('carreras.json', carreras=rs)
    return ''

@app.route('/sedes', methods = ['POST', 'GET'])
def sedes():
    matricula = config['matricula']

    if request.method == 'POST':
        label = request.form.get('label', 'option')
    else:
        label = request.args.get('label', 'option')

    db_matricula = records.Database(matricula)
    rs = db_matricula.query("SELECT * FROM RA_SEDE WHERE ACTIVA='S'", fetchall=True)
    
    if 'html' in request.headers.get('Accept'):
        return render_template('sedes.html', sedes=rs.as_dict(), label=label)
    elif 'json' in request.headers.get('Accept'):
        return render_template('sedes.json', sedes=rs)
    return ''
    
app.register_blueprint(sp.create_blueprint(), url_prefix=app.config['SP_PASE_PATH'])

PWD = os.path.abspath(os.path.dirname(__file__))
with open(f'{PWD}/app.json', 'r') as stream:
    config = yaml.safe_load(stream)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='8080', debug=True)
