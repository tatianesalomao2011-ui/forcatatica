const express = require("express");
const router = express.Router();

const ctrl = require("../controllers/cursoController");
const auth = require("../middleware/authMiddleware");

router.use(auth);

router.post("/", ctrl.create);

module.exports = router;