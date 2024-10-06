from CodeManager import *


def end_block(newline=True):
    return CodeLine("}\n        ") if newline else CodeLine("}")


def create_headers():
    code = [
        CodeLine("using System;"),
        CodeLine("using System.Collections;"),
        CodeLine("using BepInEx;"),
        CodeLine("using BepInEx.Logging;"),
        CodeLine("using HarmonyLib;"),
        CodeLine("using BepInEx.Configuration;"),
        CodeLine("using UnityEngine;"),
        CodeLine("using System.Reflection;\n "),
    ]
    return CodeBlock(code_lines=code)


def create_namespace(mod_name, mod_name_no_space):
    namespace_top = CodeBlock([
        CodeLine("namespace"),
        mod_name_no_space,
        CodeLine("\n{")
    ],
        delimiter=" "
    )
    namespace = CodeBlockWrapper(
        prefix=namespace_top,
        postfix=end_block(False)
    )
    return namespace
    

def create_namespace_contents(game):
    namespace_contents = LargeCodeBlockWrapper()
    bix_dependencies = CodeBlock()
    bix_dependencies.add_line(code_line=CodeLine("[BepInPlugin(pluginGuid, pluginName, pluginVersion)]"))
    bix_dependencies.add_line(code_line=CodeLine(
        "[BepInProcess(\"" + game + "\")]"
    ))
    bix_dependencies.add_line(code_line=CodeLine(
        "[BepInDependency(ConfigurationManager.ConfigurationManager.GUID, BepInDependency.DependencyFlags.HardDependency)]"
    ))
    namespace_contents.insert_block_before(bix_dependencies)
    namespace_contents.insert_block_after(LargeCodeBlockWrapper())
    return namespace_contents


def create_class(mod_name, mod_name_no_space):
    output = CodeBlockWrapper(
        prefix=CodeBlock(code_lines=[
            CodeLine("public class"),
            mod_name_no_space,
            CodeLine("\n    {")
        ], delimiter=" "),
        contents=LargeCodeBlockWrapper(),
        postfix=end_block(False)
    )
    output.prefix.add_line(CodeLine(": BaseUnityPlugin"), location=2)
    return output


def create_constants(mod_name, mod_name_no_space, version):
    output = LargeCodeBlockWrapper()
    plugin_guid = LargeCodeBlockWrapper([CodeLine("public const string pluginGuid =")], delimiter=" ")
    output.insert_block_after(plugin_guid)
    plugin_guid.insert_block_after(CodeBlock([CodeLine("\"org.bepinex.plugins."),
                                                  mod_name_no_space, CodeLine("\";")], delimiter=""))
    plugin_name = LargeCodeBlockWrapper([CodeLine("public const string pluginName =")], delimiter=" ")
    output.insert_block_after(plugin_name)
    plugin_name.insert_block_after(CodeBlock([CodeLine("\""), mod_name, CodeLine("\";")], delimiter=""))
    plugin_version = LargeCodeBlockWrapper([CodeLine("public const string pluginVersion =")], delimiter=" ")
    output.insert_block_after(plugin_version)
    plugin_version.insert_block_after(CodeBlock([CodeLine("\""), version, CodeLine("\";")], delimiter=""))
    return output


def create_function(head, contents=None):
    if contents is None:
        new_contents = LargeCodeBlockWrapper()
    else:
        new_contents = contents
    head = CodeLine(head + "\n        {")
    function = CodeBlockWrapper(
        prefix=head,
        contents=new_contents,
        postfix=end_block()
    )
    return function



def create_awake(mod_name, mod_name_no_space):
    output = LargeCodeBlockWrapper()
    output.insert_block_after(CodeBlock([CodeLine("Harmony.CreateAndPatchAll(typeof("), mod_name_no_space,
                                         CodeLine("));")], delimiter=""))
    output = create_function("void Awake()", contents=output)
    return output


def create_update(mod_name, mod_name_no_space):
    output = LargeCodeBlockWrapper()
    output = create_function("void Update()", contents=output)
    return output
