const sqlite3 = require("sqlite3").verbose();
const path = require("path");

const dbPath = path.join(__dirname, "forcatatica.db");

const db = new sqlite3.Database(dbPath, (err) => {
    if (err) {
        console.error("Erro ao conectar ao banco:", err);
    } else {
        console.log("Banco SQLite conectado.");
    }
});

db.serialize(() => {

    db.run(`
        CREATE TABLE IF NOT EXISTS policiais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            rgpm TEXT NOT NULL,
            discord_id TEXT NOT NULL,
            patente TEXT NOT NULL,
            cargo TEXT NOT NULL,
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    `);

    db.run(`
        CREATE TABLE IF NOT EXISTS advertencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            policial_id INTEGER,
            tipo TEXT,
            multa TEXT,
            prova TEXT,
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    `);

    db.run(`
        CREATE TABLE IF NOT EXISTS certificados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            policial_id INTEGER,
            nome_certificado TEXT,
            assinatura TEXT,
            arquivo TEXT,
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    `);

    db.run(`
        CREATE TABLE IF NOT EXISTS cursos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            policial_id INTEGER,
            nome_curso TEXT,
            data_inicio TEXT,
            data_fim TEXT,
            assinatura TEXT,
            arquivo TEXT,
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    `);

});

module.exports = db;