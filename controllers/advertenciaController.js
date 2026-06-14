const db = require("../database/database");

exports.create = (req, res) => {

    const { policial_id, tipo, multa, prova } = req.body;

    db.run(
        `INSERT INTO advertencias (policial_id, tipo, multa, prova)
         VALUES (?, ?, ?, ?)`,
        [policial_id, tipo, multa, prova],
        function (err) {

            if (err) {
                return res.status(500).json({ success: false });
            }

            res.json({ success: true });
        }
    );
};