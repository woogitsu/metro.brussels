"""Sumy PNG tego samego commita z DWOCH przebiegow — czy piksel jest ten sam.

**Skad ta bramka.** Ten sam commit dal na `tunnel-alignment (L2_E)` raz czerwien,
raz zielen: proba pierwsza padla na `BLAD: LOD 2 nie ma rzadszej siatki niz LOD 0
na: axis75`, ponowienie tego samego SHA przeszlo. Potok ZAPISUJE sume kazdego PNG
w metadanych przebiegu — ale nikt ich miedzy przebiegami nie porownuje, wiec
pytanie „czy ten sam commit daje ten sam piksel" bylo odpowiadalne z danych,
ktore juz byly, i nie odpowiadal na nie nikt.

**Ktora sume porownywac — to jest WYNIK POMIARU, nie wybor.** Metadane niosa dwie:
`sha256` calego pliku i `idat_sha256` samych pikseli. Suma calego pliku rozni sie
na KAZDEJ klatce nawet wtedy, gdy piksele sa bit-identyczne — zmierzone na parze
prob z TEJ SAMEJ maszyny. Sito na niej zglaszaloby kazda pare i liczba przestalaby
cokolwiek znaczyc, a pole „Wejscie" tej pozycji wskazywalo wlasnie na nia.

**Blendera ta bramka nie potrzebuje i to jest jej cala tresc:** liczy z danych,
ktore CI juz zapisalo. Progu bramki LOD ani potoku renderu nie rusza — jedno
i drugie wymaga Blendera i jest osobnym rozstrzygnieciem.
"""

import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "ci"))

import assert_render_sums as S  # noqa: E402

#: Przebieg i proby, z ktorych pochodza sumy nizej. Artefakty
#: `t-210-tunnel-L2_E-35332005261-1` i `-2`, ten sam SHA `bc1685b7`.
PRZEBIEG_ROZJAZDU = "35332005261"
#: Para kontrolna z JEDNEJ maszyny — przebieg `34689512388`, job `L1_B`.
PRZEBIEG_KONTROLNY = "34689512388"


#: Proba PIERWSZA (czerwona), runner `metro-wsl-DOM-NEW-03`. Klatek mniej,
#: bo czerwony job nie doszedl do konca zestawu scen.
PROBA_1_DWIE_MASZYNY = {
    "CHUNK/axis05": ("5f68c46bf018747388f7b0b1f75c1dbedd58059f819c484c6d1bafc516de5d8d",
     "aac3168b3b679edf90aea8ebc169d2a5dc15be5597fdef033a136edc9676d134"),
    "CHUNK/axis25": ("a6e6fd12dbfd711679d6cac7a5cfd9202fad037f5883f6066db6349bf7b6d315",
     "423f82bea76b18dfe137d81bd73c897e1478004cb6e9de8692ebcaf495a45280"),
    "CHUNK/axis50": ("0e477b2dd875a0c8316166a0ce6dcb09169f671bfd541246e384b58c7e4798a3",
     "db451b7c28e206d7e273b80648c8c386c7b826f5c7a20e5ab0e471c7f4861016"),
    "CHUNK/axis75": ("cb55542a29784bb77eefad86f66f80ccf0682880d2d206ce3173ed05ecccb5fe",
     "a5760bdff957b15ad6de5667819d6a17dd44914de57a9e3122b0b313a2e844b3"),
    "CHUNK/plan": ("c94994ef90dbd6d58eb2c1cf879f8c219a5faa551682ba1777e0a4e77562d22c",
     "9e63265f73d39a6954ef257e3ab3ffd83308787e893682480720112cb1ed77cf"),
    "CHUNK/section": ("dfb3ee6cb79bf723a9e046565907a37170239f2ed3cdb165411f4d1736936a9a",
     "6ad191cf1922f7b074e68e7d321aa9478ed3062131995ccf4f0cb24fe3e1946c"),
    "CHUNK/side": ("92e52e9337d4ac836b240c5f351fef545f057b7305a0e59502fef2c934a06aa6",
     "aee3598e18ecb2fbacf20f906348252baa7da1cc44f84349eb8e3f70249183aa"),
    "COL/axis05": ("929c62eadf56ea122364f94af7e39800eb05c7609fb2a5e9a14861fd6b8f9a1e",
     "ebf0ed940358389d306e0faf3ac6b54730b243c380dccbcc1012a937a28fdbd5"),
    "COL/axis25": ("1672b556fe8f45dc889a92554709175d4245a5de7312f824b30a058fd2cb2d3e",
     "b3163d211b941e41a620b72389ce6ea54ce1db7057ad77d1bc5b76bd153a4550"),
    "COL/axis50": ("8da73e38b48df1eb2b3fcec7529d0f77776e46997e4aaf6962d190ca8bde42e3",
     "219c07b95abab612a7000d676d8ba943b9526d420c91f5314d90f488d5ba1bb2"),
    "COL/axis75": ("c7e929ecc838576146bbc3fb82f560a9101103d3df7838a21127a1e53c1c8f5a",
     "9ae33e43ea7d6fb37c0a110c46430cdd30d987d2fda5284c2250462a8a1a37e7"),
    "COL/plan": ("4dbdd935270f7c229c31d83f742505d4a50ca7bc13a347eaeee1309738863ba3",
     "1141df372ded98392fd0a11d9c6a54e6081e4e1a1f95e637ca3229db23544f5d"),
    "COL/section": ("02bd7454728698dce081ad89b7b408d7a7931dda4e87ee913c55ca306d1c4529",
     "7ca2b2336ef01eaa2caaeef8c5aaa93eb1ad9f5a91e8fad10b9bffe7d7d822e6"),
    "COL/side": ("1c4c9ce10c0114f98eb83f6d0317b22c16dede4c0a91b0ce52ba21ba5c620b8b",
     "d6473dc87b4ba133ab26cce9afbcda1205ec6b5b306dd66b28af6f5b03a413c4"),
    "LOD2/axis05": ("541d425c73097f96f3ca28320e629221eb2b57fb662f406b7b0975641eff311a",
     "f8b7385b27889c31bb571d683c2d24636da310aef59f65466645326a40c974de"),
    "LOD2/axis25": ("214a2c7fd490bb3048bcea6b697bc0d1cd3268039e256ffccb953e8e9bdd6e2d",
     "1cd3997b30ad465625ecd9dd7d995e54ecfe1f774bd677ea28ad7c46d23a757b"),
    "LOD2/axis50": ("00dc30039c8483077a9de87d2454b0329a2df3f69d3e018284f57db93885877b",
     "9eb47ccf4da16f71ad3b329d40e5db3a02e7aca2ec2427f6b34024ab5368148b"),
    "LOD2/axis75": ("8ace49da2b74311273b8eacb518f12a12ab1da4405a5a133f5518a3be8ab53d4",
     "1db1888b430a3d551033fa13aad3039ee61d673ae4aa67c516919d34fc185494"),
    "LOD2/plan": ("02012c3bcdfd51280bedc19213650fc8810785422ca65115e582960437e9829c",
     "2ae739c91c6479374b952934f9e8965f1f254588659a17d63ecbff1070aed87c"),
    "LOD2/section": ("5312cf90767995fe70bf2c49ca2d21de6e08b1197b82586f362299d37553673e",
     "e796a8f5a4d444ce9aa81518a932834ce21ece3ac97108f8d422e7f9a90e6e29"),
    "LOD2/side": ("c375dffe9e6f17ef788f44e5650cbb108246a88ac2e486269da11c55e72b68d7",
     "8471e671a6a09e0a6d3591a0f5af7fe64e3a5b5244ce4f06a75c9867986b4e65"),
}

#: Proba DRUGA (zielona) tego samego SHA, runner `metro-wsl-DOM-NEW-01`.
PROBA_2_DWIE_MASZYNY = {
    "CHUNK/axis05": ("583134a9a4ebfeb484fe7d08c861b297291d5b4f079c20c22fbf624310fd75f3",
     "aac3168b3b679edf90aea8ebc169d2a5dc15be5597fdef033a136edc9676d134"),
    "CHUNK/axis25": ("f2d9ed739fc9c98ab571fe492eb5abd26e730c9b58e67ff2efc3bdc2960d7c73",
     "423f82bea76b18dfe137d81bd73c897e1478004cb6e9de8692ebcaf495a45280"),
    "CHUNK/axis50": ("705d8ebb531d3190ca0970fabc84182c79879369e9e35e3bf475bfd0b2768cfa",
     "db451b7c28e206d7e273b80648c8c386c7b826f5c7a20e5ab0e471c7f4861016"),
    "CHUNK/axis75": ("c39f3a59a55d6157fb28f8291b8bc6b98b76307bb2ce7f6211ed017687798cfb",
     "a5760bdff957b15ad6de5667819d6a17dd44914de57a9e3122b0b313a2e844b3"),
    "CHUNK/plan": ("e9adcf3c3608eccc65fa64d272dc649912db53fc5395f60110df6ebe8a7c402b",
     "9e63265f73d39a6954ef257e3ab3ffd83308787e893682480720112cb1ed77cf"),
    "CHUNK/section": ("093d0f6cc9099067f5c71b1c10e4f1b0f4103a0348b3affd84b758df5ee72776",
     "6ad191cf1922f7b074e68e7d321aa9478ed3062131995ccf4f0cb24fe3e1946c"),
    "CHUNK/side": ("5a8366779de781f1a7deedca2519dd92c28e1605741df3e57ea278ea1f3875ac",
     "aee3598e18ecb2fbacf20f906348252baa7da1cc44f84349eb8e3f70249183aa"),
    "COL/axis05": ("05b19d39cf1e260987a30ecef432721d8c81d2b1de10d5868b58d5377e55cf2a",
     "ebf0ed940358389d306e0faf3ac6b54730b243c380dccbcc1012a937a28fdbd5"),
    "COL/axis25": ("97e8d92e138658de399da6b8370769f2ed7a1f360bf9189bc5b917e6c6d48a0a",
     "b3163d211b941e41a620b72389ce6ea54ce1db7057ad77d1bc5b76bd153a4550"),
    "COL/axis50": ("fe8bd65685f00c0f400586709e270fdb43a742a2a288d773cea62d879dc317be",
     "219c07b95abab612a7000d676d8ba943b9526d420c91f5314d90f488d5ba1bb2"),
    "COL/axis75": ("62d9fbff2d3a45089064c7869a1e962ecd5cfa3954a6fef9ea3af756d9268938",
     "9ae33e43ea7d6fb37c0a110c46430cdd30d987d2fda5284c2250462a8a1a37e7"),
    "COL/plan": ("8717b9f516ffbb9c1439ede708b44dcd76f99968006d4c654e58401ce0351108",
     "1141df372ded98392fd0a11d9c6a54e6081e4e1a1f95e637ca3229db23544f5d"),
    "COL/section": ("3be21ce17f9b41dcdd69bc69c3149feaeac0c118e38c4de80d9fc532e438320e",
     "7ca2b2336ef01eaa2caaeef8c5aaa93eb1ad9f5a91e8fad10b9bffe7d7d822e6"),
    "COL/side": ("2a35ad2148b7c478ab0d208aad06022a7cbb63b520aa65b08fc8ecf72276eb6e",
     "d6473dc87b4ba133ab26cce9afbcda1205ec6b5b306dd66b28af6f5b03a413c4"),
    "L2_E/axis05": ("17f16605026eddafbbc311150046e602ce87b6d2498fc874148df8890ce36aaf",
     "649e7e4c0563bc15557569981811caeb167b39cc7eb6490f46b790af2810146b"),
    "L2_E/axis25": ("6f9fbb8fd266e7a9c8109e3425769fd8ba31e1c531e67de82236993a4c4f9272",
     "4b57e6e30dd760c2c2f2d673233d60734250c32bc9e513a2f93e327b192444d4"),
    "L2_E/axis50": ("8aa49e49218bb97402f38d705cee1e1e4f3b4c9634405d46932ed77e0bc5cd5a",
     "776e8a18f717c4ea2410449d2f975559480aa954f144eb92e8cec4f5a381cdb2"),
    "L2_E/axis75": ("bea0229bc09a00a78c53ef05c8ee09ad884f5477209b5b49c4eeea5f30358aa2",
     "b3c4b8cc8fbb439358042384c91f560e66ac0a2eb66e1b2cf5c6c06559d25d5e"),
    "L2_E/plan": ("eb08d3ed2ae8d8c48f33525c563891877797b220d10ae689c90601c3874d57ac",
     "75a72512f791459eb0974790d9cd80a23954c8db4819e9be07bda8c7e11c11a9"),
    "L2_E/section": ("2993bfc8e73a586c54237ce3ab2986eb70fbb70e54bfb3e156e5e83f2d65857d",
     "7fff671a2bdc98f379c69ff2b460d06ffc07befc008bf6fe4cc45d9744c51631"),
    "L2_E/side": ("7853b0a231e5ecd0dbb45e99c6a80c75ab75406990f0ab2ceae32cf10f7a2978",
     "e3a0aa1fe1d2d602354275b1b3da79ccabe0894bb913db74f1889de30ba05cc0"),
    "LOD2/axis05": ("2542b6075621b38dbf95411e9d03c6bf406a1638428b64cdf86e56ce555ec47b",
     "f8b7385b27889c31bb571d683c2d24636da310aef59f65466645326a40c974de"),
    "LOD2/axis25": ("37a895b2c2448d5125212e4a1bb77070ac1651ef561e05b02f16e89da1702892",
     "1cd3997b30ad465625ecd9dd7d995e54ecfe1f774bd677ea28ad7c46d23a757b"),
    "LOD2/axis50": ("ecd678afef3bd3068073e9a554a6b3b80720d7029091a3fdd7d6924ccbf73d16",
     "9eb47ccf4da16f71ad3b329d40e5db3a02e7aca2ec2427f6b34024ab5368148b"),
    "LOD2/axis75": ("2afc8b5205121647a54c9fb45dffed8085ddadf3c53c9267fe875e3694714512",
     "f51e71d2ec573286a380267a8089a78b220d9bd34ff39156d07df55140780bb1"),
    "LOD2/plan": ("6679cc14331522a484a4050f3478195e11728c734d5423e9e96a10bb73d8e565",
     "2ae739c91c6479374b952934f9e8965f1f254588659a17d63ecbff1070aed87c"),
    "LOD2/section": ("6bd0f688d772c0428a7a7650306aec804a10bd52e99bf02fa82f76c5893af124",
     "e796a8f5a4d444ce9aa81518a932834ce21ece3ac97108f8d422e7f9a90e6e29"),
    "LOD2/side": ("de0798a2d1d6c08844acdd099115d241c4ab52e8cf9684bbd95009ffdae55ce7",
     "8471e671a6a09e0a6d3591a0f5af7fe64e3a5b5244ce4f06a75c9867986b4e65"),
    "M7_GAP/approach": ("e723642f7d89dedc9a8143e24d0276b449cd77f89661cf1bc466337dc76ab583",
     "65771a7eeb96791f4dcfd39dbd4993bd4ebec2971c7d129821bce10568466a10"),
    "M7_GAP/flank": ("30378aaf2db95e39067f17fd9f32f2fe70c7d40d35b0c1d96ef271cf88bdacf8",
     "18d9267644477cca3c238ff129b9a7363c1e0ab19ebab3cf41b274339d631349"),
    "M7_GAP/gap": ("828b19d7d7edf467e122c52482929deddd7f1adb9456c519087837084c543d4a",
     "c450756ff3fdd5d0914741567065e51547bbb6655edb06b1831f8aa5d38c2369"),
    "M7_SWEPT/approach": ("338f6755ec4615b266ba76ed83acfdf506fb517e07889102036018f96a79cd58",
     "bb386299b9f7a9d44cb8cfe39d8244c0e0c9917bbe8e64505c6abeafda3806d1"),
    "M7_SWEPT/flank": ("cfb3d5da6a820fc63a4c006a2149cb9a5bc8ca062e9f61f35a0e63b78d103297",
     "9f1d7fcba293c24d5ede8d520c4d532fc4239723606523e7e55a5791ecdb3d63"),
    "M7_SWEPT/gap": ("05eb28b7dcf406eb6aaa7c70a9317ffb2dd5b7b54ae6f830abdec2a2496656f8",
     "2142064c313c67734a24b4c4a435dd6efa4f9daf18c883c641f37c300c07881c"),
    "M7_WORST/approach": ("fd4bdf646a683133f532aaa71942a872b3fa41523421aa7b6e07ba99a96a9841",
     "9b281ce2bdce0716a924eefe50ac53f1bc53ee6e5f54943e307ae6c9cfa6ed71"),
    "M7_WORST/flank": ("2eb65223f70dbc3e329000fa5fce6c65ccbd8cbf78e971f4b25ffe6c14fbd71c",
     "9cee37f1312514dd5f72031e9c1bb481f958ab021608acdb3f27960f488c1b49"),
    "M7_WORST/gap": ("24d65cba3d80650ed9d847cde0bf564ee7a7195566d37594c24833bb19b50226",
     "7b63f0acf4df64026f3c5a091e680c8865072d0810afed02c432a9c32852f54e"),
}

#: Kontrola przyrzadu — proba pierwsza pary z JEDNEJ maszyny.
PROBA_1_JEDNA_MASZYNA = {
    "CHUNK/axis05": ("438db477390b1096d1586d56b7493a78753ef6010ac64a64a162ffebeee99340",
     "1ecaf5735b3400fff4c842085ce5463604f4ca9e39f2f99bf419b2bb5a5591bd"),
    "CHUNK/axis25": ("bfd9219c4f5f73947c7e65c8a3611aa5ad6a43dcbc006b7f2d13232ef7e9e853",
     "42b4ae824ad4eca8afd535470f9eb856e32f804d5e953b9cf8b4045da5152087"),
    "CHUNK/axis50": ("4bfa08bb775bdeed2f0d6ad2e2a6c2621201fd907e8b618cabead1d4b08a324e",
     "e6206feae81761cb5785d4514dad58c30acc74989e334778a7a1ce2fef2cde94"),
    "CHUNK/axis75": ("3a128434322425aa31e4e939f33737d09a7748d4f649ba3aef138ce1d275bec4",
     "767454d95fe83487436e0c757d58888559c85fa727dcf7a6e86e03ca381f798b"),
    "CHUNK/plan": ("b041f374ca88037d991e56b810619c227303da9b43ce2abcae12c5a5f702218a",
     "d3532c1e04dc27dfb34e76a2d51af8149ef2573e8fe7cfe18a5dee0063c5477e"),
    "CHUNK/section": ("7be356af5de09789e325f30a3c5306e2a31687192ad25c991605ddd7c48aa7b9",
     "84e683dd9ec405ed49f7c4e731deb193b8121dd27a3690a3d882c9893f536431"),
    "CHUNK/side": ("c8b3d7427ad0a19754abad8ee0a0c20668f7c369c4d0ccafef3f033e741a456f",
     "382db2951e4b1a5d094317030125d99ccdf9e5e3cbe5310fefe07e5fa9c4e2c3"),
    "COL/axis05": ("bed32abcfaed3c3b1cc1cb77acc014c5ad870b1fb2be1636ac252834030afcfb",
     "de902c562cd080407ed83d49c5de761628ecd8f2a1e2deedf2e89c3af41fe7b5"),
    "COL/axis25": ("a278db17b9d65be31707b16a88af62b2c45f19f3205e65ab3b817b9a8721778b",
     "5ee0705c75b79d0836aa834392e2ac26ad89eb8ee0ca2bd4402aca82d6dcfd7e"),
    "COL/axis50": ("52be73202f53e0793325ec531d0aef4bdfbd481ae57d0341451937b32b34664d",
     "dc2e7a865cbec60e5cb72450d7895cd8b4fbf026129a72930c06dd2644e7d9e2"),
    "COL/axis75": ("df92218b01d416aff9ce897752f255b245a68fcdc0fd62c6262669dae44b2656",
     "aee810cd6069234c73492902a549ac7fb51a7ce36dcafa35fc73f02f9710e93c"),
    "COL/plan": ("b37a5a8365971f4f8a96024bb18c05ba9a2b2533da5a60bee6d6a03562259ed9",
     "77b6d54e95e011880ac38ec7ca8a47e53947ed710cf4024ed07760d1b261c659"),
    "COL/section": ("d688e66765decce1c4c1fca359b203d4b6960061129e65323cf59cf882861736",
     "7b5ce2b4509406fa7370cf61783e71e5fff9989465b419256bf3c9f85242fbbd"),
    "COL/side": ("be1f9ad5bb018f7c053797dd71ece2c2845b56bd9812c5509212a2e23cf50929",
     "267785b73727bdb5ba8ba898125849fe433584f989f6e625b369b3ae5afd9924"),
    "L1_B/axis05": ("1d21d0c201aa3706e79cbd32fa9239380d63d0c935b877fb796bb4058e213827",
     "bc4d1dc3734d108894981c829c85cfbeeb179b10212377c5364017117a7c1065"),
    "L1_B/axis25": ("2a1ae781a862d5e8acac6354c2f907eed6c4520aaf3917fcb3baefc475760212",
     "63e81c8f353d68599475e9e1c8ef429faa4d5a1e2967bb50c5cb38907dd914e2"),
    "L1_B/axis50": ("116110373f76da2fa804c4cc15be1fc54e718a162a68762ed47f8ec18caa0dfe",
     "404e828ab0aa5f701e932511fab7f5422c9ca3d1024f49c2054e2d1834a982cd"),
    "L1_B/axis75": ("295fcd04c517b9534c86df4b09bf43f404f5d0ceea36ab2fb10b082f1e762930",
     "802637130ab9b263b1f2bca85bc7f06edc534868bf4f9a6103b4e087d2485b71"),
    "L1_B/plan": ("bafb7e05e2d46ee608a5dd86b614701e9ba40ecd202f532c900f05f81b57fb6f",
     "29858c503818463dc34e33ee3cc9938d23d478ba96421fcd7130dc7135b8cec6"),
    "L1_B/section": ("9111dc939233f0212e2a3558409c7482fbaa75f8637e372c0c31fc4c1e3ed100",
     "939558ad3e2797ba4adc37fe3eb25663ecc548995c49c52445cdd4c3272c9c87"),
    "L1_B/side": ("477a800d7e6a1ef8270a298148a06a59eb190a4d108d68d7cfb9430181d23fe8",
     "f7d9412522cd11ef33cf185c9f4cfdf7d25ff822ec4b9fdb249e25285d1deb52"),
    "LOD2/axis05": ("2a9b8bcc69ae5d38cf732ba4f94d2ddb4ae9d8ad7c5c5a9dcaf2e7beb54c3d80",
     "82e28504be9a749e6e9b8323f413148506cfa667c58883d2d0dcb42e12965e32"),
    "LOD2/axis25": ("a28d4e1eeb991b92627eaf4b31e19445d79dbc951a11979b66476f08adb3febe",
     "335c262b34919ada46a39c1d82e14cc0936ccd5faff2cbf13afebc33b619e4da"),
    "LOD2/axis50": ("c675dc06d2c897a8298de4af56b6b591d8b37fac5f5718d1b659ace73f818b41",
     "ab2cf5827b68f2318256c3071fcd2452392762ff5564d65dd46a5ead4428d675"),
    "LOD2/axis75": ("7ff24c25c6aadcc6bbf84917bc7d791d8a23cb87a09c96ef63e62378a553acd0",
     "800b3015491a0f45d46ca03117abe90343f2c2386578c738b1c03c5e125e66e5"),
    "LOD2/plan": ("66fee41cc3e68737ffce38add9e0be6979f310e7886bc55c2089c9d2973d3b6f",
     "21a1aeafa8bdc459349b7d94f075fcb76eed708b7831c3ab2d9f80d035648269"),
    "LOD2/section": ("616ac57b378f1c55919c7a9860d01e26b5f748636a5308bb323be934cbf112ee",
     "f99b402bb100c5682009b52081913abf589f786751a81a3355f5210f29f34492"),
    "LOD2/side": ("c3b73548ae4473f0ac9b57de1cc4d18e45eaf9c5a2ee3148e9e3c894ee2de9da",
     "bb22a859a98cb9837c180492ac78e93a5d9318305c45d492f8b9976135c4f2e2"),
    "M7_GAP/approach": ("d8ef050b4f2ab0fe49c03545e602cb73338cc3fa8181023d8bc54610a2ee16d0",
     "8934391673619505e5cb5d61fa6d5cc00c00fe7bb9deb8725c0b8d9b5f12872e"),
    "M7_GAP/flank": ("8cf6abc6bade3a5144ea3c409df16c66c824d8b1df3a15d1b598ae011b990163",
     "bcc073655b44b2341e864ff5fbf0116d736b408cc9752a4241c9d261b6f8194c"),
    "M7_GAP/gap": ("cfbc9780c1de14e50de6fe2eb5389173f34af4a0ab18d30f8a530860f74d72b8",
     "9c86bb5bf56e2d65edbcb95566076e346640e3d286ba2624f11f22e5e038438b"),
    "M7_SWEPT/approach": ("7fa8c2612c1ada04bd5fdb04c5d3ac6c980d37f2813a8492f1c2c2ffc5a1c5bc",
     "7bfecdf4be052b0778477edfcbc2950cdb1e1934729865d58108ba81c14423f8"),
    "M7_SWEPT/flank": ("e6ace9b45a7255509493c437a12570a9cdb16c6d956241b53ba17eef1275cc09",
     "8ee6f83c1f16368c3f25eba244cd394498babcba38013f04b9db40214db845dd"),
    "M7_SWEPT/gap": ("01ac753933e496744fb58354bce679756e1abfefb021d9daf1fd750687db5ad8",
     "b51cfe6d09eedfd8f854688dd45f7a6ef00402d584e7cfdb4415abeec61a794a"),
    "M7_WORST/approach": ("43ae1b9fc5cb421b483a01466d50a344e1a4017ea1171d7d27b4fe92d03cd379",
     "8eaa200678e175d01de058d6c32bf0993b27011f4a9a668eea2ce0360b2c092d"),
    "M7_WORST/flank": ("e63b7272978793be03f4898924da57f80653c42c21f96daab8b62e9c7dfe2822",
     "b3a7b3e11c2ce7700ad714b86954ffb31b02542ceb5ad517a54b55a285874bc7"),
    "M7_WORST/gap": ("a2fe36090f74d81b1ef2524aa48c138472e30ef96ebb37685dd62e21dad5e413",
     "cdfbca5fb89615f04ccff24fb335deff3055956f81935643fce0cca696e2ec17"),
}

#: Kontrola przyrzadu — proba druga tej samej pary, ta sama maszyna.
PROBA_2_JEDNA_MASZYNA = {
    "CHUNK/axis05": ("048951be7e543901de3625f0672e77868bd27ff972d9b138b2adb7923dee0a29",
     "1ecaf5735b3400fff4c842085ce5463604f4ca9e39f2f99bf419b2bb5a5591bd"),
    "CHUNK/axis25": ("8df6a5796dcb26ac86ed05bff8c0b4ef958a7f2dcd8019b3d44c1dbbb3a8134c",
     "42b4ae824ad4eca8afd535470f9eb856e32f804d5e953b9cf8b4045da5152087"),
    "CHUNK/axis50": ("c504e01fb0b77431ae2cbf3c19fa1cf73dcacdb8cf54939062397cef11b3e58c",
     "e6206feae81761cb5785d4514dad58c30acc74989e334778a7a1ce2fef2cde94"),
    "CHUNK/axis75": ("ce2b7b33931fea660509b89e63f2ad78133da8412127536275bc520b82e7fe93",
     "767454d95fe83487436e0c757d58888559c85fa727dcf7a6e86e03ca381f798b"),
    "CHUNK/plan": ("89416cc701c01fa01965e6639019d9f38ba7e25242dc5adfafcfc361fa0e5f31",
     "d3532c1e04dc27dfb34e76a2d51af8149ef2573e8fe7cfe18a5dee0063c5477e"),
    "CHUNK/section": ("cec2b607e9db2b2479552998a3fb8d13f4be8d81fff04fc9d7171a065361f9ea",
     "84e683dd9ec405ed49f7c4e731deb193b8121dd27a3690a3d882c9893f536431"),
    "CHUNK/side": ("1aa4fe18c11821a1038dcd25265c96432f7fef45ae0c2f61077cfe2dbffa4ce8",
     "382db2951e4b1a5d094317030125d99ccdf9e5e3cbe5310fefe07e5fa9c4e2c3"),
    "COL/axis05": ("8598a32102d2ceebc5a94afdd40619041c86949b17769c30910c8a601142d5fd",
     "de902c562cd080407ed83d49c5de761628ecd8f2a1e2deedf2e89c3af41fe7b5"),
    "COL/axis25": ("71ca9d645ee71cd7838d8e22f3b52fe45f98fb9048513bddc310ebf559193115",
     "5ee0705c75b79d0836aa834392e2ac26ad89eb8ee0ca2bd4402aca82d6dcfd7e"),
    "COL/axis50": ("b5de9a06a89c48790a5b49a1b7a6e6d173260051e33a9742dd788ae157eeea0a",
     "dc2e7a865cbec60e5cb72450d7895cd8b4fbf026129a72930c06dd2644e7d9e2"),
    "COL/axis75": ("aa24c0e9f1ed70ef946cc450380307798daf5aef08a3d25248645404385380cf",
     "aee810cd6069234c73492902a549ac7fb51a7ce36dcafa35fc73f02f9710e93c"),
    "COL/plan": ("4b9f9d5c4baeab77e0b3bff39e4d9a296cf8b7ffc8b14cc86a1940ccb3cb2965",
     "77b6d54e95e011880ac38ec7ca8a47e53947ed710cf4024ed07760d1b261c659"),
    "COL/section": ("fdd716803cb3d2fee0189268525e87f388dde84f277475d660e17e1e3fdf5819",
     "7b5ce2b4509406fa7370cf61783e71e5fff9989465b419256bf3c9f85242fbbd"),
    "COL/side": ("747d7117098e6e1767922a059c677b1182c4a99c1b6bb84d950c0e684dd4ae8e",
     "267785b73727bdb5ba8ba898125849fe433584f989f6e625b369b3ae5afd9924"),
    "L1_B/axis05": ("ad525bc8eb15dba6bcb7f4c1dff93b3bdc4800f34b0eef5d91473183725d0b37",
     "bc4d1dc3734d108894981c829c85cfbeeb179b10212377c5364017117a7c1065"),
    "L1_B/axis25": ("bb687e2af8d63022201fa8ea817e24d913f708a20240c47ec6b6db40fa45df95",
     "63e81c8f353d68599475e9e1c8ef429faa4d5a1e2967bb50c5cb38907dd914e2"),
    "L1_B/axis50": ("1b0e3c785fb4c4ee30814753f48ef0d451467a8ce1cf40849e6ed3580e486182",
     "404e828ab0aa5f701e932511fab7f5422c9ca3d1024f49c2054e2d1834a982cd"),
    "L1_B/axis75": ("6c2965f2331f7dd0d7aed8bb3c8362fa26daade8c40a7e30cea96d98c1646f59",
     "802637130ab9b263b1f2bca85bc7f06edc534868bf4f9a6103b4e087d2485b71"),
    "L1_B/plan": ("59c5f707ccf8de8f2866e50182914633145b1249d4e4709b9cd314e4f98caee9",
     "29858c503818463dc34e33ee3cc9938d23d478ba96421fcd7130dc7135b8cec6"),
    "L1_B/section": ("ea0d22c6be9da25299ccb3ee4ad0ddb96af5ea7ed65b7a4aa172d01a1345dcd8",
     "939558ad3e2797ba4adc37fe3eb25663ecc548995c49c52445cdd4c3272c9c87"),
    "L1_B/side": ("862b32d05d9de63b27558a7ef2a4f4dd58d39e974b6bc5d256faf1d739be63be",
     "f7d9412522cd11ef33cf185c9f4cfdf7d25ff822ec4b9fdb249e25285d1deb52"),
    "LOD2/axis05": ("a2e76b8a0abbc7b13d69b0a9ff86940b3a89a3600d9c31d19374f694c274f459",
     "82e28504be9a749e6e9b8323f413148506cfa667c58883d2d0dcb42e12965e32"),
    "LOD2/axis25": ("b2a6a5b90a9b328f493d76d52e3685dc81bb2da406df8dcb58b1b5d7c2486b62",
     "335c262b34919ada46a39c1d82e14cc0936ccd5faff2cbf13afebc33b619e4da"),
    "LOD2/axis50": ("4a94d46ba9e4fbf5ebb9023736cb0f45d6140702e1f179eec88bee19dbb523af",
     "ab2cf5827b68f2318256c3071fcd2452392762ff5564d65dd46a5ead4428d675"),
    "LOD2/axis75": ("648f2e507d3436ebde227adf2ce8105ed93ddf3cc53d8c7b1ba9605d0d210773",
     "800b3015491a0f45d46ca03117abe90343f2c2386578c738b1c03c5e125e66e5"),
    "LOD2/plan": ("1a002a5928dd94d56e9fff81844b902ed7d7193d9b594977b5d6d23e9e0668da",
     "21a1aeafa8bdc459349b7d94f075fcb76eed708b7831c3ab2d9f80d035648269"),
    "LOD2/section": ("bf6d6f18714d350f55cef7f0826a66a0b45657ebf667c10b52de9bf53e7cdadb",
     "f99b402bb100c5682009b52081913abf589f786751a81a3355f5210f29f34492"),
    "LOD2/side": ("7fe3b679c41d7c3fe119c3d4cccbc184f74ad4ea13d748b24d54f24865513b37",
     "bb22a859a98cb9837c180492ac78e93a5d9318305c45d492f8b9976135c4f2e2"),
    "M7_GAP/approach": ("a1fb1f447f86a3325f9ca9337a00cdffa944d1863dfe9eb3f81adcccb4315bc0",
     "8934391673619505e5cb5d61fa6d5cc00c00fe7bb9deb8725c0b8d9b5f12872e"),
    "M7_GAP/flank": ("e72a6eb5f05834148999fc81a9ad2dd1cb7f90ef6c0cf35e44d97cc375777c76",
     "bcc073655b44b2341e864ff5fbf0116d736b408cc9752a4241c9d261b6f8194c"),
    "M7_GAP/gap": ("e11b174f3c3ed98958b8e658c889b4066d1eb38660fc6f8f5c13b27510ad08fb",
     "9c86bb5bf56e2d65edbcb95566076e346640e3d286ba2624f11f22e5e038438b"),
    "M7_SWEPT/approach": ("e613bd605bbcb2b2816d1b4267ece7b4696340c4daeab2e0374f96cd4857e126",
     "7bfecdf4be052b0778477edfcbc2950cdb1e1934729865d58108ba81c14423f8"),
    "M7_SWEPT/flank": ("c0e06c390442604b1d6bd7255e031b101e4e0c107c295c4718def62e488929a6",
     "8ee6f83c1f16368c3f25eba244cd394498babcba38013f04b9db40214db845dd"),
    "M7_SWEPT/gap": ("98a25b9b30c6d707f1acde235c318e6b1e51c4b38a747a50b92fc66c3e8889d7",
     "b51cfe6d09eedfd8f854688dd45f7a6ef00402d584e7cfdb4415abeec61a794a"),
    "M7_WORST/approach": ("0edec8fb7bb5308112b4b068db444fbd0ab0506748ea81536e3fcf2fbdd903f1",
     "8eaa200678e175d01de058d6c32bf0993b27011f4a9a668eea2ce0360b2c092d"),
    "M7_WORST/flank": ("66eff393ac49974f6ca58c8f484c747e998db03cbbd6cf49b5a85efe82146ec9",
     "b3a7b3e11c2ce7700ad714b86954ffb31b02542ceb5ad517a54b55a285874bc7"),
    "M7_WORST/gap": ("27b8236739615af546fc8eabb4464daaefd4784b19343e8d3915d4c42e30887e",
     "cdfbca5fb89615f04ccff24fb335deff3055956f81935643fce0cca696e2ec17"),
}

#: Klatka, ktora sie rozjezdza. Przybita co do nazwy: gdyby rozjechala sie inna,
#: bramka ma o tym powiedziec, a nie tylko podac, ze liczba sie zgadza.
ROZJECHANA_KLATKA = "LOD2/axis75"

#: Ile klatek rozni sie po PIKSELACH w parze dwumaszynowej, a ile po sumie CALEGO
#: PLIKU. Druga liczba jest tu trescia, a nie ciekawostka: rowna sie liczbie klatek
#: wspolnych, czyli sito na sumie pliku zglasza wszystko.
ROZJAZDOW_PO_PIKSELACH = 1
KLATEK_WSPOLNYCH = 21


def test_para_z_DWOCH_maszyn_rozjezdza_sie_na_jednej_klatce():
    """**Pierwsza z trzech liczb, ktorych zadalo pole „Wyjscie".**

    Kontrola negatywna sita: para o roznych sumach MA zostac zgloszona. Dzis nie
    zglasza tego nic, bo sumy sa zapisywane, a nie porownywane miedzy przebiegami.
    """
    wspolne, rozne, tylko1, tylko2 = S.porownaj(
        PROBA_1_DWIE_MASZYNY, PROBA_2_DWIE_MASZYNY)
    assert len(wspolne) == KLATEK_WSPOLNYCH, (
        "klatek wspolnych jest %d, a pomiar dal %d" % (len(wspolne), KLATEK_WSPOLNYCH))
    assert len(rozne) == ROZJAZDOW_PO_PIKSELACH, (
        "klatek o roznych pikselach jest %d, a pomiar dal %d: %s"
        % (len(rozne), ROZJAZDOW_PO_PIKSELACH, rozne))
    assert rozne == [ROZJECHANA_KLATKA], (
        "rozjezdza sie inna klatka niz przybita: %s wobec %s"
        % (rozne, ROZJECHANA_KLATKA))
    assert not tylko1, (
        "proba pierwsza ma klatke, ktorej nie ma druga: %s" % tylko1)
    assert tylko2, (
        "proba druga nie ma ani jednej klatki wiecej — a czerwony job przerwal "
        "przed koncem zestawu scen, wiec ma ich miec mniej")


def test_para_z_JEDNEJ_maszyny_jest_bit_w_bit_ta_sama():
    """**Kontrola przyrzadu: sito ma NIE zglaszac kazdej pary.**

    Bez tej polowy liczba wyzej nic nie znaczy — sito zglaszajace wszystko
    zglosiloby i rozjazd, i jego brak.
    """
    wspolne, rozne, tylko1, tylko2 = S.porownaj(
        PROBA_1_JEDNA_MASZYNA, PROBA_2_JEDNA_MASZYNA)
    assert not tylko1 and not tylko2, (
        "para kontrolna ma rozny zestaw klatek, wiec nie jest para: %s / %s"
        % (tylko1, tylko2))
    assert rozne == [], (
        "para z TEJ SAMEJ maszyny rozjechala sie na %d klatkach — kontrola "
        "przyrzadu upadla i liczba z testu wyzej przestaje cokolwiek znaczyc: %s"
        % (len(rozne), rozne))
    assert len(wspolne) > KLATEK_WSPOLNYCH, (
        "para kontrolna ma %d klatek, czyli nie wiecej niz para badana — "
        "kontrola na mniejszej probie jest slabsza niz to, co kontroluje"
        % len(wspolne))


def test_suma_CALEGO_PLIKU_zglasza_KAZDA_pare_i_dlatego_sie_jej_nie_uzywa():
    """**Trzecia liczba, i to ona rozstrzyga, ktora sume potok ma porownywac.**

    Pole „Wejscie" tej pozycji wskazuje na `sha256` kazdego PNG. Zmierzone:
    ta suma rozni sie na KAZDEJ klatce takze tam, gdzie piksele sa bit-identyczne,
    wiec sito zbudowane na niej zglasza wszystko — i rozjazd, i jego brak.
    """
    _w1, po_pliku_2, _a, _b = S.porownaj(
        PROBA_1_DWIE_MASZYNY, PROBA_2_DWIE_MASZYNY, po_pikselach=False)
    wspolne_k, po_pliku_k, _c, _d = S.porownaj(
        PROBA_1_JEDNA_MASZYNA, PROBA_2_JEDNA_MASZYNA, po_pikselach=False)
    assert len(po_pliku_2) == KLATEK_WSPOLNYCH, (
        "suma calego pliku rozni sie na %d z %d klatek pary dwumaszynowej"
        % (len(po_pliku_2), KLATEK_WSPOLNYCH))
    assert len(po_pliku_k) == len(wspolne_k), (
        "suma calego pliku rozni sie na %d z %d klatek pary z TEJ SAMEJ maszyny — "
        "gdyby nie roznila sie na wszystkich, mozna by jej uzywac, a caly powod "
        "wyboru `idat_sha256` bylby inny" % (len(po_pliku_k), len(wspolne_k)))


def test_czytnik_metadanych_czyta_to_samo_co_przybite_sumy():
    """**Kontrola przyrzadu na CZYTNIKU, a nie na danych.**

    Sumy wyzej sa przepisane z artefaktow. Gdyby czytnik metadanych zmienil
    ksztalt klucza albo pole, ktore czyta, testy wyzej nadal by przechodzily,
    bo porownuja slowniki miedzy soba — a nie z tym, co czytnik zwraca z pliku.
    """
    import json
    import tempfile
    klucz, (sha, idat) = sorted(PROBA_2_JEDNA_MASZYNA.items())[0]
    prefiks, _, kamera = klucz.partition("/")
    with tempfile.TemporaryDirectory() as katalog:
        sciezka = os.path.join(katalog, "%s_metadata.json" % prefiks)
        with open(sciezka, "w", encoding="utf-8") as uchwyt:
            json.dump({"prefix": prefiks,
                       "cameras": [{"id": kamera, "sha256": sha,
                                    "idat_sha256": idat}]}, uchwyt)
        odczyt = S.sumy_z_metadanych([sciezka])
    assert odczyt == {klucz: (sha, idat)}, (
        "czytnik metadanych zwraca co innego niz to, co stoi w pliku (przebiegi "
        "%s i %s): %s" % (PRZEBIEG_ROZJAZDU, PRZEBIEG_KONTROLNY, odczyt))


# Strażnik `__main__` — bez niego `python3 tools/tests/<moduł>.py` kończył się
# kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
