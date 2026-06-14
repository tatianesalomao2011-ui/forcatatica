require("dotenv").config();

function authMiddleware(req, res, next) {

    // login do sistema (simples e único)
    const user = req.headers["x-user"];
    const pass = req.headers["x-pass"];

    if (
        user === process.env.LOGIN_USER &&
        pass === process.env.LOGIN_PASSWORD
    ) {
        return next();
    }

    return res.status(401).json({
        success: false,
        message: "Não autorizado"
    });
}

module.exports = authMiddleware;