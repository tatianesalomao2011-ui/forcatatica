const db = require("../database/database");

exports.create = (req, res) => {

    const { policial_id, nome_certificado, assinatura } = req.body;

    db.run(
        `INSERT INTO certificados (policial_id, nome_certificado, assinatura)
         VALUES (?, ?, ?)`,
        [policial_id, nome_certificado, assinatura],
        function (err) {

            if (err) {
                return res.status(500).json({ success: false });
            }

            res.json({ success: true });
        }
    );
};