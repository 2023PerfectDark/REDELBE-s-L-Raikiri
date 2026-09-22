The readme will be mainly about the topic of creating new costume/hairs. Don't worry, it is not complex.
New costume/hairs mods will be called "Layer2 mods" from now on.

Before further explanation, I will tell how to convert a typical replacer costume mod into a Layer2 mod in few steps:

1) Create a new folder and give it the name of your mod. 
2) Copy the MaterialEditor and CharacterEditor of the replacer mod there (there may be only one of them or both, that's fine).
3) Rename the MaterialEditor folder as "Material", and the CharacterEditor folder as "Character".
4) Create a file called "mod.ini" with the following content (no need to copy the ;;;;)

;;;;;;;;;;;
[General]
type = costume

[Costume]
slot = XXX_COS_NNN
;;;;;;;;;;;

where XXX_COS_NNN is the slot, eg. "MAR_COS_007" for Marie Rose Deluxe.

5) Copy the folder into REDELBE/Layer2. And that's it, the mod is done!

----------------

Hair mods
Hair mods follow the same aproach.
The ini would be as follow instead:

;;;;;;;;
[General]
type = hair

[Hair]
slot = XXX_HAIR_NNN 
;;;;;;;;;;;

where XXX_HAIR_NNN is the hair slot, eg., "KAS_HAIR_001".

--------------

More about the ini file. The mod.ini can have up to 4 sections: [General], [Costume], [Hair], and [Face]

The [General] section is optional. If it doesn't exist, or if "type" in General is not specified, REDELBE assumes it is a costume mod.

The Costume section is mandatory in costume mods, and it is ignored in hair mods.
The Hair section is mandatory in hair mods, and it is optional in costume mods. Yes, costume mods can use the Hair section, but usually you won't do it.
A costume mod that includes a Hair section is still considered a costume mod, which means it still needs to be selected at costume selection screen, and not in hair/glasses selection screen.

The [Face] section is optional in both, costume and hair mods. Usually you won't be using it at all. But the "slot" for face would be something like "KOK_FACE_001", so the same pattern.


The [General], [Hair] and [Face] section all have a field called "slot" that is mandatory if the section exists, and which specify the slot they work in.
There is also another field -which is optional and that you will rarely use- called "work", that allows to impersonate another costume, even from other character.

That feature can give some compatibility problems, so it must only be used with care, but in case you wonder what it is, consider the following mod.ini example:

;;;;;;;;
[General]
type = costume

[Costume]
slot = AYA_COS_002
work = KAS_COS_005
;;;;;;;;

Such a mod, would make the KAS_COS_005 costume available for Ayane in the AYA_COS_002 slot.
However, if the mod on the other player were modifying KAS_COS_005, well, the changes would apply to both, due to this it is recommeded to act with caution when using the "work" feature.
(same goes for hair)

--------------

And that't it. I recommend you to download the crappy example mods that I made. They may not be sophisticated, but they are "educative" to learn about the possibilities of Layer2 mods.
Each of them have some readme with comments for modders.
Lately, I would recommend modders to activate the log feature of REDELBE. (set "log_virtual", "log_internal" and "log_external" to true in REDELBE.ini)

The REDELBE log can be useful to troubleshoot problems, knowing which files are being loaded, and which not (and from where they are being loaded).

