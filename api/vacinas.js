const https = require('https');
const nodemailer = require('nodemailer');

function githubRequest(method, body, token) {
  return new Promise((resolve, reject) => {
    const data = body ? JSON.stringify(body) : null;
    const options = {
      hostname: 'api.github.com',
      path: '/repos/Cainho-pt-br/Vacinas/contents/vacinas.json',
      method: method,
      headers: {
        'Authorization': `token ${token}`,
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'vacinas-app',
        'Content-Type': 'application/json',
        ...(data && { 'Content-Length': Buffer.byteLength(data) })
      }
    };
    const req = https.request(options, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => resolve({ status: res.statusCode, body: body ? JSON.parse(body) : {} }));
    });
    req.on('error', reject);
    if (data) req.write(data);
    req.end();
  });
}

async function enviarEmail(novos, totalFila) {
  const user = process.env.GMAIL_USER;
  const pass = process.env.GMAIL_APP_PASSWORD;
  if (!user || !pass) { console.log('Email nao configurado'); return; }

  const transporter = nodemailer.createTransport({ service: 'gmail', auth: { user, pass } });

  const agora = new Date().toLocaleString('pt-BR', {
    timeZone: 'America/Sao_Paulo',
    day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit',
  });

  const linhas = novos.map((p, i) =>
    '<tr><td style="padding:6px 12px;border:1px solid #ddd;text-align:center">' + (i+1) + '</td>' +
    '<td style="padding:6px 12px;border:1px solid #ddd">' + (p.nome||'') + '</td>' +
    '<td style="padding:6px 12px;border:1px solid #ddd">' + (p.vacina||'') + '</td>' +
    '<td style="padding:6px 12px;border:1px solid #ddd">' + (p.via||'') + '</td></tr>'
  ).join('');

  const html = '<div style="font-family:Arial,sans-serif;max-width:600px">' +
    '<h2 style="color:#1D9E75">Nova lista de vacinas recebida</h2>' +
    '<p><strong>' + novos.length + '</strong> paciente(s) enviado(s) em <strong>' + agora + '</strong>.</p>' +
    '<p>Fila total aguardando impressao: <strong>' + totalFila + ' paciente(s)</strong>.</p>' +
    '<table style="border-collapse:collapse;width:100%;margin:16px 0">' +
    '<tr style="background:#f5f5f3"><th style="padding:8px 12px;border:1px solid #ddd">#</th>' +
    '<th style="padding:8px 12px;border:1px solid #ddd">Nome</th>' +
    '<th style="padding:8px 12px;border:1px solid #ddd">Vacina</th>' +
    '<th style="padding:8px 12px;border:1px solid #ddd">Via</th></tr>' +
    linhas + '</table>' +
    '<p style="color:#888;font-size:12px">Email automatico do sistema de etiquetas.</p></div>';

  await transporter.sendMail({
    from: '"Lista de Vacinas" <' + user + '>',
    to: user,
    subject: 'Nova lista de vacinas - ' + novos.length + ' paciente(s) (' + agora + ')',
    html: html,
  });
  console.log('Email enviado para', user);
}

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, PUT, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();

  const token = process.env.GITHUB_TOKEN;
  if (!token) return res.status(500).json({ error: 'Token nao configurado' });

  try {
    if (req.method === 'GET') {
      const r = await githubRequest('GET', null, token);
      if (r.status === 404) return res.status(200).json({ exists: false, data: [] });
      const decoded = Buffer.from(r.body.content.replace(/\n/g, ''), 'base64').toString('utf-8');
      return res.status(200).json({ exists: true, sha: r.body.sha, data: JSON.parse(decoded) });
    }

    if (req.method === 'PUT') {
      const { novosDados } = req.body;
      let existente = [];
      let sha = null;
      const get = await githubRequest('GET', null, token);
      if (get.status === 200) {
        sha = get.body.sha;
        const decoded = Buffer.from(get.body.content.replace(/\n/g, ''), 'base64').toString('utf-8');
        existente = JSON.parse(decoded);
      }

      const novaLista = existente.concat(novosDados);
      const conteudo = Buffer.from(JSON.stringify(novaLista, null, 2)).toString('base64');
      const body = { message: 'Nova lista: ' + novosDados.length + ' paciente(s)', content: conteudo, ...(sha && { sha }) };

      const put = await githubRequest('PUT', body, token);
      if (put.status !== 200 && put.status !== 201) {
        return res.status(400).json({ error: put.body.message || 'Erro ao salvar' });
      }

      enviarEmail(novosDados, novaLista.length).catch(e => console.error('Erro email:', e.message));
      return res.status(200).json({ ok: true, total: novaLista.length });
    }

    return res.status(405).json({ error: 'Metodo nao permitido' });
  } catch (e) {
    return res.status(500).json({ error: e.message });
  }
};
