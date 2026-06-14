const db = require("../database/database");

exports.create = (req, res) => {

    const { nome, rgpm, discord, patente, cargo } = req.body;

    db.run(
        `INSERT INTO policiais (nome, rgpm, discord_id, patente, cargo)
         VALUES (?, ?, ?, ?, ?)`,
        [nome, rgpm, discord, patente, cargo],
        function (err) {

            if (err) {
                return res.status(500).json({ success: false });
            }

            res.json({ success: true, id: this.lastID });
        }
    );
};

exports.list = (req, res) => {

    db.all(`SELECT * FROM policiais`, [], (err, rows) => {

        if (err) {
            return res.status(500).json([]);
        }

        res.json(rows);
    });
};

exports.remove = (req, res) => {

    db.run(
        `DELETE FROM policiais WHERE id = ?`,
        [req.params.id],
        (err) => {

            if (err) {
                return res.status(500).json({ success: false });
            }

            res.json({ success: true });
        }
    );
};