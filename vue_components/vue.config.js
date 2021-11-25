const BundleTracker = require("webpack-bundle-tracker");

const DEV_HOST = process.env.DEV_HOST ?? 'localhost';
const VUE_DEV_PORT = process.env.VUE_DEV_PORT ?? '8080';

module.exports = {
    publicPath: process.env.NODE_ENV === 'production' ? '/content' : `http://${DEV_HOST}:${VUE_DEV_PORT}`,
    runtimeCompiler: true,

    chainWebpack: config => {

        config.optimization
            .splitChunks(false)

        config
            .plugin('BundleTracker')
            .use(BundleTracker, [{filename: '../vue_components/webpack-stats.json'}])

        config.resolve.alias
            .set('__STATIC__', 'static')

        config.devServer
            .host(DEV_HOST)
            .port(VUE_DEV_PORT)
            .hotOnly(true)
            .watchOptions({poll: 1000})
            .https(false)
            .headers({"Access-Control-Allow-Origin": ["\*"]})
            }
        };