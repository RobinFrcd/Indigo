rd /S /Q %1

mkdir %1

copy LICENSE.GPL %1\
copy indigo.h %1\
copy renderer\indigo-renderer.h %1\
copy dll\%2\Release\indigo.dll %1\
copy %2\Release\indigo.lib %1\
copy renderer\%2\Release\indigo-renderer.lib %1\
copy renderer\dll\%2\Release\indigo-renderer.dll %1\
copy ..\graph\%2\Release\graph.lib %1\
copy ..\molecule\%2\Release\molecule.lib %1\
copy ..\reaction\%2\Release\reaction.lib %1\
copy ..\layout\%2\Release\layout.lib %1\
copy ..\render2d\%2\Release\render2d.lib %1\
copy ..\zlib-src\%2\ReleaseDll\zlib.dll %1\

zip -r -9 %1.zip %1
