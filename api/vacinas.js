export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();

  const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
  const API_URL = 'https://api.github.com/repos/Cainho-pt-br/Vacinas/contents/vacinas.json';
  const headers = {
    'Authorization': `token ${GITHUB_TOKEN}`,
    'Accept': 'application/vnd.github.v3+json',
    'Content-Type': 'application/json'
  };

  try {
    if (req.method === 'GET') {
      const resp = await fetch(API_URL, { headers });
      if (resp.status === 404) return res.status(200).json({ exists: false, data: [] });
      const json = await resp.json();
      const decoded = Buffer.from(json.content.replace(/\n/g, ''), 'base64').toString('utf-8');
      return res.status(200).json({ exists: true, sha: json.sha, data: JSON.parse(decoded) });
    }

    if (req.method === 'PUT') {
      const { novosDados, sha } = req.body;
      const getResp = await fetch(API_URL, { headers });
      let existente = [];
      let shaAtual = sha;
      if (getResp.ok) {
        const getJson = await getResp.json();
        shaAtual = getJson.sha;
        const decoded = Buffer.from(getJson.content.replace(/\n/g, ''), 'base64').toString('utf-8');
        existente = JSON.parse(decoded);
      }
      const novaLista = existente.concat(novosDados);
      const conteudo = Buffer.from(JSON.stringify(novaLista, null, 2)).toString('base64');
      const body = {
        message: `Nova lista: ${novosDados.length} paciente(s) — ${new Date().toLocaleString('pt-BR')}`,
        content: conteudo,
        ...(shaAtual && { sha: shaAtual })
      };
      const putResp = await fetch(API_URL, { method: 'PUT', headers, body: JSON.stringify(body) });
      if (!putResp.ok) {
        const err = await putResp.json();
        return res.status(400).json({ error: err.message });
      }
      return res.status(200).json({ ok: true, total: novaLista.length });
    }

    if (req.method === 'DELETE') {
      const { sha } = req.body;
      const body = { message: 'Fila processada — arquivo removido', sha };
      const delResp = await fetch(API_URL, { method: 'DELETE', headers, body: JSON.stringify(body) });
      if (!delResp.ok) {
        const err = await delResp.json();
        return res.status(400).json({ error: err.message });
      }
      return res.status(200).json({ ok: true });
    }

    return res.status(405).json({ error: 'Método não permitido' });

  } catch (e) {
    return res.status(500).json({ error: e.message });
  }
}
