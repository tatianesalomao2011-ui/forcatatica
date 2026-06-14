require("dotenv").config();

exports.login = (req, res) => {

    const { username, password } = req.body;

    if (
        username === process.env.LOGIN_USER &&
        password === process.env.LOGIN_PASSWORD
    ) {
        return res.json({ success: true });
    }

    return res.status(401).json({ success: false });
};