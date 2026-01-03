## 0.2.0 (2026-01-03)


### Features

* Add camelCase tool name normalization ([ac52d61](https://github.com/opencontextprotocol/ocp-python/commit/ac52d61fec2844cc281805b1a490e5e886cc6b7d))
* add GitHub Actions workflows for testing and publishing ([e12f608](https://github.com/opencontextprotocol/ocp-python/commit/e12f608eda73fdf573253042930a3ae1c1a55855))
* add OpenAPI spec validation and update tests ([954c73b](https://github.com/opencontextprotocol/ocp-python/commit/954c73b8e35c14e92710224ac829e29b0e3b964e))
* add polymorphic keyword handling in $ref resolution ([a225d9e](https://github.com/opencontextprotocol/ocp-python/commit/a225d9e43686d38367ab8d4a22b390481b0ba8db))
* add support for resolving $ref references in OpenAPI specs ([a1b5a09](https://github.com/opencontextprotocol/ocp-python/commit/a1b5a0974a0011a220cb45bd3b13ed9eeb24318a))
* add support for Swagger 2.0 specification ([562e8e6](https://github.com/opencontextprotocol/ocp-python/commit/562e8e695d5d21fd48227bf3fec0513ca5e21345))
* add tag filtering to discover_api method ([008c256](https://github.com/opencontextprotocol/ocp-python/commit/008c256f85d5c7d83915d2554f20f4c83690bfc4))
* add tests for OCPRegistry initialization ([2ab4eec](https://github.com/opencontextprotocol/ocp-python/commit/2ab4eece498c3222c1369e03031b1d2ce86e6a9e))
* add tool name validation and logging ([375a109](https://github.com/opencontextprotocol/ocp-python/commit/375a10943ab117945deae021f058332c9fb6e03a))
* enhance OCPAgent to support authentication headers ([5f7c619](https://github.com/opencontextprotocol/ocp-python/commit/5f7c619e3f8f126b76a025de031446bee3bb70c8))
* enhance resource filtering to support path prefix ([e9360c0](https://github.com/opencontextprotocol/ocp-python/commit/e9360c0883b23bc2d30da21c8c3e86bb7b5d574f))
* implement resource-based filtering in discover_api ([fe75293](https://github.com/opencontextprotocol/ocp-python/commit/fe7529373eb73efffec60f1b4a543a56cc05e3e4))
* normalize API names for case-insensitive matching ([a011102](https://github.com/opencontextprotocol/ocp-python/commit/a011102a333d7d2e5d007a94b2b6aab32757faed))
* refine resource filtering to enforce exact matches ([e7897ba](https://github.com/opencontextprotocol/ocp-python/commit/e7897ba152fb6e87c3d59d43febd1fec23ed25f5))
* support loading OpenAPI specs from local files ([60ec98d](https://github.com/opencontextprotocol/ocp-python/commit/60ec98dd395d8a9e4a17b061bfbba882c0dd2895))


### Bug Fixes

* add headers parameter to register_api method ([89ea5cd](https://github.com/opencontextprotocol/ocp-python/commit/89ea5cd980dcf41c39af53632df64c85f5b1ba23))
* Add missing OCP_USER header encoding to match JS implementation ([8894746](https://github.com/opencontextprotocol/ocp-python/commit/889474644a721b7b54ee4c987b7e7dd832cec9dd))
* correct project name in pyproject.toml ([9effdd1](https://github.com/opencontextprotocol/ocp-python/commit/9effdd1794fc0cc8436a273f068955cca804e0aa))
* correct project name in pyproject.toml ([8d95b09](https://github.com/opencontextprotocol/ocp-python/commit/8d95b0944357efc6301a6f0c2adff33062cf143f))
* enhance logging in OCPHTTPClient interactions ([38a4406](https://github.com/opencontextprotocol/ocp-python/commit/38a4406203e3e8746471aec9fb604f401958a8c4))
* improve $ref resolution with memoization ([125005c](https://github.com/opencontextprotocol/ocp-python/commit/125005cbd10ea96200277b2ee516e64c0e3018a0))
* provide default description for operations without one ([ee221b0](https://github.com/opencontextprotocol/ocp-python/commit/ee221b08710537945416d8a2a7c095451a0bdead))
* remove OpenAPI spec validator and validation method ([2201ee6](https://github.com/opencontextprotocol/ocp-python/commit/2201ee6dc006ec929995d28ae80a1a46980f76d7))
* remove unused packages from poetry.lock ([11b0f82](https://github.com/opencontextprotocol/ocp-python/commit/11b0f8281e6a25d22a14557cc1b1940ea974b6ee))
* update .gitignore to include additional patterns ([6a81d1b](https://github.com/opencontextprotocol/ocp-python/commit/6a81d1bf9927962f15a223b834a657ce8e4e765d))
* update default registry URL to correct endpoint ([873b6b3](https://github.com/opencontextprotocol/ocp-python/commit/873b6b37b350137f35ce1f2058d7b99267f39e32))
* update default registry URL to opencontextprotocol ([10914c9](https://github.com/opencontextprotocol/ocp-python/commit/10914c9db376e501e499ced32cd40974f8960b5f))
* update default registry URL to use constant ([8e3da54](https://github.com/opencontextprotocol/ocp-python/commit/8e3da547562b3eb78a1a8608f23f0593ebff12da))
* update header constants and tests for clarity ([9d65edc](https://github.com/opencontextprotocol/ocp-python/commit/9d65edc3a42d61adb4f91e6fff65f82cf291d08f))
* update repository URLs in configuration files ([41b6f46](https://github.com/opencontextprotocol/ocp-python/commit/41b6f469192070416fe32e71ed2fe653b87ce1cc))

