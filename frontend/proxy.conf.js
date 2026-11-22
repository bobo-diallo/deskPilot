// Le navigateur appelle /api/... sur le serveur Angular, qui transmet au backend en retirant
// le préfixe /api. En Docker, BACKEND_URL vaut http://backend:8000 ; en local, le port 8010.
module.exports = {
  '/api': {
    target: process.env.BACKEND_URL || 'http://localhost:8010',
    pathRewrite: { '^/api': '' },
    changeOrigin: true,
  },
};
