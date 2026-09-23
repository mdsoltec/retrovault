# Base de cheats do RetroVault Web

Esta pasta segue o formato de **Dynamic Cheats do EmulatorJS**.

## Como funciona

O `play.html` configura:

```js
EJS_cheatPath = 'cheats/';
```

Além disso, o RetroVault Web carrega os JSONs antes de iniciar o loader e converte os registros para `EJS_cheats`, garantindo compatibilidade com a versão do EmulatorJS utilizada no projeto.

São carregados:

- `cheats/cheats.json` — base global opcional;
- `cheats/<core>.json` — base específica do core.

Os arquivos já criados para o RetroVault Web são:

| Core do EmulatorJS | Arquivo |
|---|---|
| `nes` | `nes.json` |
| `snes` | `snes.json` |
| `gba` | `gba.json` |
| `gbc` | `gbc.json` |
| `gb` | `gb.json` |
| `n64` | `n64.json` |
| `pcsx_rearmed` | `pcsx_rearmed.json` |
| `segaMD` | `segaMD.json` |
| `segaCD` | `segaCD.json` |
| `segaGG` | `segaGG.json` |
| `nds` | `nds.json` |
| `fbneo` | `fbneo.json` |

## Formato do JSON

A chave deve ser o título/nome do arquivo da ROM, sem a extensão. O valor é uma lista de cheats:

```json
{
  "Super Mario World (USA)": [
    { "desc": "Vidas infinitas", "code": "C222-D4DD" },
    { "desc": "Tempo infinito", "code": "C264-64D7" }
  ]
}
```

O formato de `code` precisa ser compatível com o sistema e com a revisão da ROM. Para códigos compostos, mantenha o formato aceito pelo RetroArch/Libretro, por exemplo usando `+` entre partes quando aplicável.

## Adicionar um cheat

1. Abra o JSON correspondente ao core.
2. Use o nome base da ROM como chave. Exemplos:
   - `Super Mario World (USA).sfc` → `Super Mario World (USA)`;
   - `garou.zip` → `garou`.
3. Adicione objetos com `desc` e `code`.
4. Salve o arquivo e recarregue o jogo.
5. No menu do EmulatorJS, abra **Cheats** e ative/desative o código.

O botão que normalmente abriria o menu genérico do EmulatorJS foi redirecionado para o popup de **Cheats**. Assim, o ícone de menu abre diretamente os códigos carregados. Se um jogo ou uma revisão não tiver códigos cadastrados, o popup ainda permite inserir um cheat manualmente.

## Base ampliada

Os arquivos ativos foram ampliados usando a base comunitária [libretro-database](https://github.com/libretro/libretro-database):

- `cheats/<core>.json` contém uma seleção curada de até 12 códigos úteis por jogo, para manter o menu fácil de usar;
- `cheats/libretro/<core>.json` guarda a base completa convertida encontrada para o catálogo atual;
- `cheats/libretro/manifest.json` registra a fonte, data de geração e quantidade de códigos por core.

O carregador do `play.html` continua usando somente os arquivos ativos. A pasta `libretro/` funciona como arquivo completo para futuras curadorias.

## Observações

- JSON não aceita comentários; use este README para anotações.
- Códigos podem variar entre versões USA, Europe, Japan e revisões da ROM.
- Alguns sistemas, especialmente Arcade, usam formatos de cheat diferentes. Quando a base Libretro não fornece um `cheatN_code` compatível com o EmulatorJS, o código não é importado automaticamente.
- Mesmo quando o código é convertido corretamente, teste-o na revisão exata da ROM; alguns códigos precisam de reinício para desativar.
