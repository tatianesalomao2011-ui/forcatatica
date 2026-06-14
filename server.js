const express = require("express");

const app = express();

/* TESTE SIMPLES */
app.get("/", (req, res) => {
    res.send("FORÇA TÁTICA ONLINE - SERVIDOR OK");
});

app.get("/api/status", (req, res) => {
    res.json({ status: "ok" });
});

/* PORTA CORRETA RAILWAY */
const PORT = process.env.PORT || 3000;

app.listen(PORT, "0.0.0.0", () => {
    console.log("Servidor rodando na porta", PORT);
});