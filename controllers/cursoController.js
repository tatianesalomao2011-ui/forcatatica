const db = require("../database/database");

exports.create = (req, res) => {

    const { policial_id, nome_curso, data_inicio, data_fim, assinatura } = req.body;

    db.run(
        `INSERT INTO cursos (policial_id, nome_curso, data_inicio, data_fim, assinatura)
         VALUES (?, ?, ?, ?, ?)`,
        [policial_id, nome_curso, data_inicio, data_fim, assinatura],
        function (err) {

            if (err) {
                return res.status(500).json({ success: false });
            }

            res.json({ success: true });
        }
    );
};