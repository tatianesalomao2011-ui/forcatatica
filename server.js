require("dotenv").config();

const express = require("express");
const cors = require("cors");
const path = require("path");

const app = express();

require("./database/database");

app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// STATIC
app.use(express.static(path.join(__dirname, "public")));

/* =========================
   ROTAS API
========================= */

const authRoutes = require("./routes/authRoutes");
const policialRoutes = require("./routes/policialRoutes");
const advertenciaRoutes = require("./routes/advertenciaRoutes");
const certificadoRoutes = require("./routes/certificadoRoutes");
const cursoRoutes = require("./routes/cursoRoutes");

app.use("/api/auth", authRoutes);
app.use("/api/policiais", policialRoutes);
app.use("/api/advertencias", advertenciaRoutes);
app.use("/api/certificados", certificadoRoutes);
app.use("/api/cursos", cursoRoutes);

/* =========================
   DASHBOARD (RESUMO)
========================= */

const db = require("./database/database");

app.get("/api/dashboard", (req, res) => {

    db.serialize(() => {

        db.get("SELECT COUNT(*) as total FROM policiais", (err, p) => {

            db.get("SELECT COUNT(*) as total FROM advertencias", (err2, a) => {

                db.get("SELECT COUNT(*) as total FROM certificados", (err3, c) => {

                    db.get("SELECT COUNT(*) as total FROM cursos", (err4, cu) => {

                        res.json({
                            policiais: p.total,
                            advertencias: a.total,
                            certificados: c.total,
                            cursos: cu.total
                        });

                    });

                });

            });

        });

    });
});

/* =========================
   FRONTEND SPA
========================= */

app.get("*", (req, res) => {
    res.sendFile(path.join(__dirname, "public", "index.html"));
});

/* =========================
   START SERVER
========================= */

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
    console.log(`Servidor rodando na porta ${PORT}`);
});