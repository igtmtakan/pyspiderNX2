const express = require('express');
const bodyParser = require('body-parser');
const app = express();

// 新しい構文でのミドルウェア設定
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static('public'));

// セキュリティ設定の追加
app.use(helmet());