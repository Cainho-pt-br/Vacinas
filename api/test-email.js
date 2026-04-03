const nodemailer = require('nodemailer');

module.exports = async (req, res) => {
  const user = process.env.GMAIL_USER;
  const pass = process.env.GMAIL_APP_PASSWORD;

  if (!user || !pass) {
    return res.status(500).json({ error: 'Variaveis nao configuradas', hasUser: !!user, hasPass: !!pass });
  }

  try {
    const transporter = nodemailer.createTransport({ service: 'gmail', auth: { user, pass } });
    await transporter.sendMail({
      from: '"Teste Vacinas" <' + user + '>',
      to: user,
      subject: 'Teste de email - sistema de vacinas',
      text: 'Se voce recebeu este email, o sistema funciona!',
    });
    return res.status(200).json({ ok: true, message: 'Email enviado para ' + user });
  } catch (e) {
    return res.status(500).json({ error: e.message, code: e.code });
  }
};
