# Documentation for the Isle Goblin Mod Maker

# Important Stuff:

## Errors

* If you have any errors with the mod maker itself feel free to join [Isle Goblin Modding Discord Sever](https://discord.gg/vKy7YHPMmx).
* The [Isle Goblin Wiki modding section](https://islegoblin.wiki/wiki/Modding_for_Isle_Goblin#Errors) has a really good error handling page. Please note that some of these errors, including the NetStandard2.0 -> 2.1 error has been fixed and will be deployed in update v1.1.0 (semantic versioning)

Common Errors:

### Netstandard error

* If you get **an error** that has something to do with **netstandard** then go to your **Isle Goblin Mod Maker folder resources>csporjtemplate**
* In this file **change the 3rd line** from `<TargetFramework>netstandard2.0</TargetFramework>` to `<TargetFramework>netstandard2.1</TargetFramework>`
* **Now re-build your mod** and it should work if you code itself has no errors

## Mod Menu not showing up

* Go to [BepinEX ConfigManager](https://thunderstore.io/c/valheim/p/Azumatt/Official_BepInEx_ConfigurationManager/)
* Then click **Manual Download**
* Now **extract** the **downloaded** **zip**
* **After** it's **done extracting**, you can **delete the zip*
* **Open** up the **extracted folder**
* Inside of that folder, **open BepinEX>plugins>ConfigurationManager**
* **Make sure you have the Isle Goblin Playtest folder open as well**
* Inside of your **Isle Goblin folder** open **BepinEX>plugins**
* Now drag and drop the **ConfigurationManager.dll** from the **ConfigurationManager** folder **to the Isle Goblin Playtest>BepinEX>plugins folder**
* Start up Isle Goblin and you should be good to go.
