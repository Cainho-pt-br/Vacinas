const https = require('https');

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

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, PUT, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();

  const token = process.env.GITHUB_TOKEN;
  if (!token) return res.status(500).json({ error: 'Token não configurado' });

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
      const body = {
        message: `Nova lista: ${novosDados.length} paciente(s)`,
        content: conteudo,
        ...(sha && { sha })
      };

      const put = await githubRequest('PUT', body, token);
      if (put.status !== 200 && put.status !== 201) {
        return res.status(400).json({ error: put.body.message || 'Erro ao salvar' });
      }
      return res.status(200).json({ ok: true, total: novaLista.length });
    }

    return res.status(405).json({ error: 'Método não permitido' });

  } catch (e) {
    return res.status(500).json({ error: e.message });
  }
};
