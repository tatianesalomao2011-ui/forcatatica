require("dotenv").config();

const express = require("express");
const cors = require("cors");
const path = require("path");

const app = express();

require("./database/database");

app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.use(express.static(path.join(__dirname, "public")));

/* ROTAS */
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

/* DASHBOARD */
const db = require("./database/database");

app.get("/api/dashboard", (req, res) => {
    db.get("SELECT COUNT(*) as total FROM policiais", (e1, p) => {
        db.get("SELECT COUNT(*) as total FROM advertencias", (e2, a) => {
            db.get("SELECT COUNT(*) as total FROM certificados", (e3, c) => {
                db.get("SELECT COUNT(*) as total FROM cursos", (e4, cu) => {

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

/* FRONT */
app.get("*", (req, res) => {
    res.sendFile(path.join(__dirname, "public", "index.html"));
});

/* START (IMPORTANTE) */
const PORT = process.env.PORT || 3000;

app.listen(PORT, "0.0.0.0", () => {
    console.log("Servidor rodando na porta", PORT);
});