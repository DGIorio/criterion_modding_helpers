#-*- coding:utf-8 -*-

bl_info = {
    "name": "Criterion modding helpers",
    "description": "Helping tools for developing mods for games from Criterion Games",
    "author": "DGIorio",
    "version": (3, 2, 0),
    "blender": (3, 1, 0),
    "location": "3D View > Add > Criterion modding tools",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "support": "COMMUNITY",
    "category": "Mesh"}


import bpy
import bmesh
import os
import struct
import binascii
from bpy.props import (
	BoolProperty,
	EnumProperty,
)
from bpy_extras.io_utils import (
	orientation_helper,
	axis_conversion,
)
from mathutils import Matrix, Vector, Quaternion
import math #pi
import numpy as np
import zlib
try:
	from mw_custom_materials import custom_shaders as custom_shaders_mw, get_default_material_parameters as get_default_material_parameters_mw
except:
	print("WARNING: mw_custom_materials.py not found in Blender addons folder. Custom material data will not be available.")
try:
	from hp_custom_materials import custom_shaders as custom_shaders_hp, get_default_material_parameters as get_default_material_parameters_hp
except:
	print("WARNING: hp_custom_materials.py not found in Blender addons folder. Custom material data will not be available.")


def main_bp():
	shared_dir = os.path.join(BurnoutLibraryGet(), "BPR_Library_PC")
	shared_shader_dir = os.path.join(os.path.join(shared_dir, "SHADERS"), "Shader")
	
	for material in bpy.data.materials:
		shader_type = "Vehicle_Opaque_PaintGloss_Textured"
		shader_type_default = shader_type
		
		if not "shader_type" in material:
			material["shader_type"] = shader_type
		else:
			shader_type = material["shader_type"]
		
		if shader_type == "":
			shader_type = shader_type_default
			material["shader_type"] = shader_type_default
		
		mShaderId, shader_type = get_mShaderID(shader_type, "GraphicsSpec")
		material["shader_type"] = shader_type
		
		shader_path = os.path.join(shared_shader_dir, mShaderId + ".dat")
		_, required_raster_types, num_material_states_shader, material_constants, muNumVertexShaderConstantsInstances, mafVertexShaderConstantsInstanceData, mauVertexShaderNamesHash, muNumPixelShaderConstantsInstances, mafPixelShaderConstantsInstanceData, mauPixelShaderNamesHash = read_shader(shader_path)
		
		if muNumVertexShaderConstantsInstances > 0:
			if not "VertexShaderNamesHash" in material:
				material["VertexShaderNamesHash"] = mauVertexShaderNamesHash
			for i in range(0, muNumVertexShaderConstantsInstances):
				if not "VertexShaderConstantsInstanceData_entry_%d" % i in material:
					material["VertexShaderConstantsInstanceData_entry_%d" % i] = mafVertexShaderConstantsInstanceData[i]
		
		if muNumPixelShaderConstantsInstances > 0:
			if not "PixelShaderNamesHash" in material:
				material["PixelShaderNamesHash"] = mauPixelShaderNamesHash
			for i in range(0, muNumPixelShaderConstantsInstances):
				if not "PixelShaderConstantsInstanceData_entry_%d" % i in material:
					material["PixelShaderConstantsInstanceData_entry_%d" % i] = mafPixelShaderConstantsInstanceData[i]
	
	return {'FINISHED'}


def main_mw():
	shared_dir = os.path.join(NFSMWLibraryGet(), "NFSMW_Library_PC")
	shared_shader_dir = os.path.join(os.path.join(shared_dir, "SHADERS"), "Shader")
	
	for material in bpy.data.materials:
		shader_type = "VehicleNFS13_BodyPaint_Livery"
		shader_type_default = shader_type
		
		if not "shader_type" in material:
			material["shader_type"] = shader_type
		else:
			shader_type = material["shader_type"]
		
		if shader_type == "":
			shader_type = shader_type_default
			material["shader_type"] = shader_type_default
		
		mShaderId, shader_type = get_mShaderID_mw(shader_type, "GraphicsSpec")
		material["shader_type"] = shader_type
		
		shader_path = os.path.join(shared_shader_dir, mShaderId + "_83.dat")
		shader_description_, mVertexDescriptorId, num_sampler_states, required_raster_types, shader_parameters, material_constants = read_shader_mw(shader_path)
		
		try:
			status, material_parameters = get_default_material_parameters_mw(shader_type)
			material_parameters = [list(param) for param in material_parameters]
		except:
			print("WARNING: get_default_material_parameters function not found. Not all custom data will be available.")
			status, material_parameters = get_default_material_parameters_mw_copy(shader_type)
		
		if status == 0:
			parameters_Data = material_parameters[3][:]
			parameters_Names = material_parameters[4][:]
		else:
			parameters_Data = shader_parameters[3][:]
			parameters_Names = shader_parameters[4][:]
		
		for i in range(0, len(parameters_Names)):
			if not parameters_Names[i] in material:
				material[parameters_Names[i]] = parameters_Data[i][:]
			
			if parameters_Names[i] in ('MaterialDiffuse', 'LightmapColour', 'LitWindowColour', 'materialDiffuse', 'tiling1Diffuse', 'tiling3Diffuse', 'tiling2Diffuse', 'decal_Diffuse',
										   'Colour', 'Line_Diffuse', 'MaterialSpecular', 'algaeColour', 'LightmappedLightsGreenChannelColour', 'PbrMaterialScuffColour', 'EmissiveColour',
										   'PbrMaterialDiffuseColour', 'LightmappedLightsAlphaChannelColour', 'LightmappedLightsBlueChannelColour', 'LightmappedLightsRedChannelColour',
										   'PbrMaterialSpecularColour', 'ReversingColour', 'mExternalGlassColour', 'TaillightColour', 'BrakeColour', 'HeadlightColour', 'PbrMaterialDustColour',
										   'mCrackedGlassSpecularColour', 'PbrMaterialDirtColour', 'DebugOverride_GlassVolumeColour', 'RunningColour', 'MaterialColour_SimpleMultiply'):
				property_manager = material.id_properties_ui(parameters_Names[i])
				property_manager.update(subtype = 'COLOR')
	
	return {'FINISHED'}


def main_hp():
	shared_dir = os.path.join(NFSHPLibraryGet(), "NFSHPR_Library_PC")
	shared_shader_dir = os.path.join(os.path.join(shared_dir, "SHADERS"), "Shader")
	resource_version = "NFSHPR_PC"
	
	for material in bpy.data.materials:
		shader_type = "VehicleNFS13_BodyPaint_Livery"
		shader_type_default = shader_type
		
		if not "shader_type" in material:
			material["shader_type"] = shader_type
		else:
			shader_type = material["shader_type"]
		
		if shader_type == "":
			shader_type = shader_type_default
			material["shader_type"] = shader_type_default
		
		mShaderId, shader_type = get_mShaderID_hp(shader_type, "GraphicsSpec")
		material["shader_type"] = shader_type
		
		shader_path = os.path.join(shared_shader_dir, mShaderId + "_83.dat")
		shader_description_, mVertexDescriptorId, num_sampler_states, required_raster_types, shader_parameters, material_constants = read_shader_hp(shader_path, resource_version)
		
		try:
			status, material_parameters = get_default_material_parameters_hp(shader_type)
			material_parameters = [list(param) for param in material_parameters]
		except:
			print("WARNING: get_default_material_parameters function not found. Not all custom data will be available.")
			status, material_parameters = get_default_material_parameters_hp_copy(shader_type)
		
		if status == 0:
			parameters_Data = material_parameters[3][:]
			parameters_Names = material_parameters[4][:]
		else:
			parameters_Data = shader_parameters[3][:]
			parameters_Names = shader_parameters[4][:]
		
		for i in range(0, len(parameters_Names)):
			if not parameters_Names[i] in material:
				material[parameters_Names[i]] = parameters_Data[i][:]
			
			if parameters_Names[i] in ('DirtTint', 'materialDiffuse', 'LightmappedLightsGreenChannelColour', 'LightmappedLightsBlueChannelColour',
										'LightmappedLightsRedChannelColour', 'window_Tint', 'pearlescentColour', 'ReversingColour', 'UnusedColour',
										'mCrackedGlassSpecularColour', 'BrakeColour', 'RunningColour', 'mGlassColour', 'OverlayA_Diffuse', 'DiffuseB',
										'OverlayB_Diffuse', 'DiffuseA', 'Colour', 'gEmissiveColour', 'tiling1Diffuse', 'tiling3Diffuse', 'tiling2Diffuse',
										'decal_Diffuse', 'mMaterialDiffuse', 'Line_Diffuse', 'DiffuseColour', 'EmissiveColour', 'algaeColour', 'mExternalGlassColour'):
				property_manager = material.id_properties_ui(parameters_Names[i])
				property_manager.update(subtype = 'COLOR')
	
	return {'FINISHED'}


def load_vehicle_data_mw(m):
	shared_dir = os.path.join(NFSMWLibraryGet(), "NFSMW_Library_PC")
	shared_vehicles_dir = os.path.join(shared_dir, "VEHICLES")
	shared_character_dir = os.path.join(shared_dir, "CHARACTERS")
	characterLibrary = os.path.join(shared_dir, "CHARACTERS", "ALL_CHARS.blend")
	
	#m = axis_conversion(from_forward='-Y', from_up='Z', to_forward='-Z', to_up='X').to_4x4()
	
	for main_collection in bpy.context.scene.collection.children:
		is_hidden = bpy.context.view_layer.layer_collection.children.get(main_collection.name).hide_viewport
		is_excluded = bpy.context.view_layer.layer_collection.children.get(main_collection.name).exclude
		
		if is_hidden or is_excluded:
			print("WARNING: skipping main collection %s since it is hidden or excluded." % (main_collection.name))
			print("")
			continue
		
		print("Reading scene data for main collection %s..." % (main_collection.name))
			
		# GraphicsSpec
		if "resource_type" in main_collection:
			resource_type = main_collection["resource_type"]
		else:
			print("WARNING: collection %s is missing parameter %s. Define one of the followings: 'GraphicsSpec', 'CharacterSpec'." % (main_collection.name, '"resource_type"'))
			resource_type = "GraphicsSpec"
			#return {"CANCELLED"}
		
		try:
			collections_types = {collection["resource_type"] : collection for collection in main_collection.children}
		except:
			print("WARNING: some collection is missing parameter %s. Define one of the followings: 'GraphicsSpec', 'WheelGraphicsSpec', 'PolygonSoupList', 'Character', 'CharacterSpec'." % '"resource_type"')
			collections_types = {}
			for collection in main_collection.children:
				try:
					collections_types[collection["resource_type"]] = collection
				except:
					collections_types["GraphicsSpec"] = collection
				
			#return {"CANCELLED"}
		
		if resource_type == "GraphicsSpec":
			vehicle_name = main_collection.name
			vehicle_number = vehicle_name.replace("VEH", "").replace("HI", "").replace("LO", "").replace("TR", "").replace("GR", "").replace("MS", "")
			vehicle_number = vehicle_number.replace("veh", "").replace("hi", "").replace("lo", "").replace("tr", "").replace("gr", "").replace("ms", "").replace("_", "")
			
			try:
				test = int(vehicle_number)
			except:
				print("ERROR: main_collection's name is in the wrong format. Use something like VEH_122672_HI or VEH_122672_LO.")
			mGraphicsSpecId = int_to_id(vehicle_number)
			graphicsspec_collection = collections_types["GraphicsSpec"]
			
			collections = [graphicsspec_collection,]
			
			vehicle_dir = os.path.join(shared_vehicles_dir, vehicle_name)
			skeleton_dir = os.path.join(vehicle_dir, "Skeleton")
			genesysobject_dir = os.path.join(vehicle_dir, "GenesysObject")
			graphicsspec_dir = os.path.join(vehicle_dir, "GraphicsSpec")
			graphicsspec_path = os.path.join(graphicsspec_dir, mGraphicsSpecId + ".dat")
			for file in os.listdir(graphicsspec_dir):
				if mGraphicsSpecId in file:
					graphicsspec_path = os.path.join(graphicsspec_dir, file)
					break
			
			if "Skeleton" in collections_types:
				pass
			else:
				_, _, _, mSkeletonId, _ = read_graphicsspec_mw(graphicsspec_path)
				skeleton_path = os.path.join(skeleton_dir, mSkeletonId + ".dat")
				Skeleton = []
				if os.path.isfile(skeleton_path) == True:
					Skeleton = read_skeleton_mw(skeleton_path)
				
				if len(Skeleton) > 0:
					skeleton_collection2 = bpy.data.collections.new(vehicle_number + "_Skeleton")
					skeleton_collection2["resource_type"] = "Skeleton"
					skeleton_collection2.color_tag = "COLOR_07"
					main_collection.children.link(skeleton_collection2)
					
					armature_created = False
					try:
						cm_armature_rig = bpy.context.scene.objects[mSkeletonId]
						armature_created = True
					except:
						cm_armature = bpy.data.armatures.new(mSkeletonId)
						cm_armature_rig = bpy.data.objects.new(mSkeletonId, cm_armature)
					
					skeleton_collection2.objects.link(cm_armature_rig)
					bpy.context.view_layer.objects.active = cm_armature_rig
					bpy.ops.object.mode_set(mode='EDIT', toggle=False)
					edit_bones = cm_armature_rig.data.edit_bones
					
					skeleton_method = "hinges"
					if skeleton_method == "joints":
						for i, sensor in enumerate(Skeleton):
							sensor_index, mSensorPosition, mSensorRotation, parent_sensor, older_sensor, child_sensor, has_ik, sensor_hash = sensor
							sensor_Transform = Matrix.LocRotScale(mSensorPosition, Quaternion([mSensorRotation[3], mSensorRotation[0], mSensorRotation[1], mSensorRotation[2]]), None)
							
							cm_bone_name = "Sensor_%03d" % sensor_index
							b = edit_bones.new(cm_bone_name)
							b.head = mSensorPosition
							#b.tail = mSensorPosition
							
							if parent_sensor != -1:
								b.parent = edit_bones["Sensor_%03d" % parent_sensor]
								b.use_connect = False
								#b.use_connect = True
								
								for sensor_ in Skeleton:
									if sensor_[0] == parent_sensor:
										#b.head = sensor_[1]
										b.tail = sensor_[1]
										break
							
							tail, roll = mat3_to_vec_roll(sensor_Transform.to_3x3())
							b.roll = roll
							
							if b.length < 1e-3:
								b.tail = b.head + Vector([0.0, 0.0, 0.12])
								#b.head = b.tail + Vector([0.0, 0.0, 0.12])
							b["hash"] = int_to_id(sensor_hash)
							if has_ik == True:
								b["has_ik"] = has_ik
					
					elif skeleton_method == "hinges":
						for i, sensor in enumerate(Skeleton):
							sensor_index, mSensorPosition, mSensorRotation, parent_sensor, older_sensor, child_sensor, has_ik, sensor_hash = sensor
							quat_a = Quaternion([mSensorRotation[3], mSensorRotation[0], mSensorRotation[1], mSensorRotation[2]])
							sensor_Transform = Matrix.LocRotScale(mSensorPosition, quat_a, None)
							
							if quat_a[0] < 0:
								bone_direction = Vector((-1.0, -1.0, -1.0))
							else:
								bone_direction = Vector((1.0, 1.0, 1.0))
							
							cm_bone_name = "Sensor_%03d" % sensor_index
							b = edit_bones.new(cm_bone_name)
							b.head = mSensorPosition
							
							if parent_sensor != -1:
								b.parent = edit_bones["Sensor_%03d" % parent_sensor]
								b.use_connect = False
								#b.use_connect = True
							
							#tail, roll = mat3_to_vec_roll(sensor_Transform.to_3x3())
							
							boneLength = 0.2
							b.tail = Vector(sensor_Transform.col[1][0:3])*bone_direction*boneLength + b.head
							#b.roll = roll
							
							if b.length < 1e-3:
								b.tail = b.head + Vector([0.0, 0.0, 0.12])
								#b.head = b.tail + Vector([0.0, 0.0, 0.12])
							b["hash"] = int_to_id(sensor_hash)
							if has_ik == True:
								b["has_ik"] = has_ik
					
					bpy.ops.object.mode_set(mode='OBJECT')	
					mTransform = Matrix([[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]).transposed()
					cm_armature_rig.matrix_world = m @ mTransform
					if armature_created == False:
						cm_armature.display_type = 'WIRE'
						#cm_armature.show_names = True
						cm_armature.show_bone_custom_shapes = True
					cm_armature_rig.show_in_front = True
					
					# Bone shape
					try:
						bone_sphere = bpy.data.objects["dgi_sphere_skeleton"]
					except:
						bone_sphere = create_sphere(name="dgi_sphere_skeleton", radius=0.025)
						bone_sphere.use_fake_user = True
					
					for b in cm_armature_rig.pose.bones:
						b.custom_shape = bone_sphere
						b.use_custom_shape_bone_size = False
					
					#for renderable_object in renderable_objects:
					#	modifier = renderable_object.modifiers.new(name=mSkeletonId, type='ARMATURE')
					#	modifier.object = cm_armature_rig
			
			if "Effects" in collections_types:
				pass
			elif "Effect" in collections_types:
				pass
			else:
				## Loading effects from vehicle file
				instances_effects, instances_effects2 = read_effects_graphicsspec(graphicsspec_path)
				
				# Creating effects object
				# Creating collection
				effects_collection = bpy.data.collections.new(vehicle_number + "_Effects")
				effects_collection["resource_type"] = "Effects"
				effects_collection.color_tag = "COLOR_05"
				main_collection.children.link(effects_collection)
				
				# Creating effect object
				for effect_instance in instances_effects2:
					EffectId, i, effectsLocation, EffectData = effect_instance
					
					effect_object_name = "Effect_%d.%s" % (i, vehicle_number)
					effect_empty = bpy.data.objects.new(effect_object_name, None)
					effects_collection.objects.link(effect_empty)
					
					effect_empty['EffectId'] = EffectId
					#effect_empty['EffectData'] = EffectData
					
					effect_empty.matrix_world = m @ effect_empty.matrix_world
					
					for j, effectLocation in enumerate(effectsLocation):
						effect_object_name2 = "Effect_%d_copy_%d.%s" % (i, j, vehicle_number)
						effect_empty2 = bpy.data.objects.new(effect_object_name2, None)
						effect_empty2.parent = effect_empty
						
						mLocatorMatrix = Matrix([[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [*effectLocation[0], 1.0]]).transposed()
						effect_empty2.matrix_world = m @ mLocatorMatrix
						effect_empty2.rotation_mode = 'QUATERNION'
						effect_empty2.rotation_quaternion = [effectLocation[1][3], effectLocation[1][0], effectLocation[1][1], effectLocation[1][2]]
						
						effect_empty2.empty_display_type = 'SINGLE_ARROW'
						effect_empty2.empty_display_size = 0.5
						
						if EffectData != []:
							effect_empty2['sensor_hash'] = int_to_id(EffectData[j])
						
						effects_collection.objects.link(effect_empty2)
			
			if "Character" in collections_types:
				pass
			elif "Driver" in collections_types:
				pass
			else:
				genesysobject_path = os.path.join(genesysobject_dir, mGraphicsSpecId + ".dat")
				instances_character = read_genesysobject1(genesysobject_dir, genesysobject_path)
				
				## Creating driver object
				# Creating collection
				character_collection = bpy.data.collections.new(vehicle_number + "_Driver")
				character_collection["resource_type"] = "Character"
				character_collection.color_tag = "COLOR_06"
				main_collection.children.link(character_collection)
				
				# Creating driver object
				mCharacterSpecID, characterOffset = instances_character
				
				driver_object_name = "%s_Driver" % (vehicle_number)
				driver_empty = bpy.data.objects.new(driver_object_name, None)
				driver_empty["CharacterSpecID"] = mCharacterSpecID
				character_collection.objects.link(driver_empty)
				
				armature_object = None
				if os.path.isfile(characterLibrary) == True:
					with bpy.data.libraries.load(characterLibrary, link=False) as (data_from, data_to):
						data_to.collections = [col for col in data_from.collections if col.startswith(str(mCharacterSpecID))]
						if data_to.collections == []:
							data_to.collections = [[col for col in data_from.collections if col.endswith("Character")][0]]
					
					for library_collection in data_to.collections:
						driver_objects = library_collection.objects
						for driver_object in driver_objects:
							if driver_object.type == "ARMATURE":
								character_collection.objects.link(driver_object)
								mLocatorMatrix = Matrix([[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [*characterOffset, 1.0]]).transposed()
								driver_object.matrix_world = m @ mLocatorMatrix
								driver_object.hide_set(True)
								armature_object = driver_object
								armature_matrix = mLocatorMatrix
							else:
								for child in driver_object.children:
									if child["renderable_index"] == 0:
										child.parent = driver_empty
										character_collection.objects.link(child)
										break
				
				mLocatorMatrix = Matrix([[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [*characterOffset, 1.0]]).transposed()
				
				driver_empty.matrix_world = m @ mLocatorMatrix
				
				if armature_object != None:
					armature_object.parent = driver_empty
					armature_object.matrix_world = m @ armature_matrix
	
	return {'FINISHED'}


def read_genesysobject1(genesysobject_dir, genesysobject_path):
	with open(genesysobject_path, "rb") as f:
		#f.seek(0xF0, 0)
		f.seek(-0x8, 2)
		muOffset = struct.unpack("<H", f.read(0x2))[0]
		while muOffset != 0x2C:
			f.seek(-0x12, 1)
			muOffset = struct.unpack("<H", f.read(0x2))[0]
		f.seek(-0xA, 1)
		mResourceId = bytes_to_id(f.read(0x4))
	
	genesysobject_path = os.path.join(genesysobject_dir, mResourceId + ".dat")
	with open(genesysobject_path, "r+b") as f:
		f.seek(0x10, 0)
		characterOffset = list(struct.unpack("<fff", f.read(0xC)))
		f.seek(0x24, 0)
		mCharacterSpecID = struct.unpack("<i", f.read(0x4))[0]
		
		instances_character = [mCharacterSpecID, characterOffset]
	
	return instances_character


def read_effects_graphicsspec(graphicsspec_path):
	instances_effects = []
	instances_effects2 = []
	with open(graphicsspec_path, "rb") as f:
		f.seek(0x1C, 0)
		effects_count = struct.unpack("<i", f.read(0x4))[0]
		mpEffectsId = struct.unpack("<i", f.read(0x4))[0]
		mpEffectsTable = struct.unpack("<i", f.read(0x4))[0]
		
		for i in range(0, effects_count):
			f.seek(mpEffectsId + 0x4*i, 0)
			EffectsId = struct.unpack("<i", f.read(0x4))[0]
			
			f.seek(mpEffectsTable + 0xC*i, 0)
			effect_count = struct.unpack("<i", f.read(0x4))[0]
			effect_pointer = struct.unpack("<i", f.read(0x4))[0]
			unknown_pointer = struct.unpack("<i", f.read(0x4))[0]
			
			#EffectData = []
			#if unknown_pointer != 0:
			#	f.seek(unknown_pointer, 0)
			#	EffectData = struct.unpack("<IIII", f.read(0x10))
			
			effectsLocation = []
			EffectData = []
			for j in range(0, effect_count):
				f.seek(effect_pointer + 0x20*j, 0)
				effectRotation = struct.unpack("<ffff", f.read(0x10))
				effectLocation = struct.unpack("<fff", f.read(0xC))
				
				effectsLocation.append([effectLocation, effectRotation])
				
				if unknown_pointer != 0:
					f.seek(unknown_pointer + 0x4*j, 0)
					effect_data = struct.unpack("<I", f.read(0x4))[0]
					EffectData.append(effect_data)
				
				instances_effects.append([EffectsId, i, j, effectLocation[:], EffectData[:]])
			
			instances_effects2.append([EffectsId, i, effectsLocation[:], EffectData[:]])
	
	return (instances_effects, instances_effects2)


def load_vehicle_data_hp(m):
	shared_dir = os.path.join(NFSHPLibraryGet(), "NFSHPR_Library_PC")
	shared_vehicles_dir = os.path.join(shared_dir, "VEHICLES")
	shared_character_dir = os.path.join(shared_dir, "CHARACTERS")
	characterLibrary = os.path.join(shared_dir, "CHARACTERS", "ALL_CHARS.blend")
	resource_version = "NFSHPR_PC"
	
	#m = axis_conversion(from_forward='-Y', from_up='Z', to_forward='-Z', to_up='X').to_4x4()
	
	for main_collection in bpy.context.scene.collection.children:
		is_hidden = bpy.context.view_layer.layer_collection.children.get(main_collection.name).hide_viewport
		is_excluded = bpy.context.view_layer.layer_collection.children.get(main_collection.name).exclude
		
		if is_hidden or is_excluded:
			print("WARNING: skipping main collection %s since it is hidden or excluded." % (main_collection.name))
			print("")
			continue
		
		print("Reading scene data for main collection %s..." % (main_collection.name))
			
		# GraphicsSpec
		if "resource_type" in main_collection:
			resource_type = main_collection["resource_type"]
		else:
			print("WARNING: collection %s is missing parameter %s. Define one of the followings: 'GraphicsSpec', 'CharacterSpec'." % (main_collection.name, '"resource_type"'))
			resource_type = "GraphicsSpec"
			#return {"CANCELLED"}
		
		try:
			collections_types = {collection["resource_type"] : collection for collection in main_collection.children}
		except:
			print("WARNING: some collection is missing parameter %s. Define one of the followings: 'GraphicsSpec', 'WheelGraphicsSpec', 'PolygonSoupList', 'Character', 'CharacterSpec'." % '"resource_type"')
			collections_types = {}
			for collection in main_collection.children:
				try:
					collections_types[collection["resource_type"]] = collection
				except:
					collections_types["GraphicsSpec"] = collection
				
			#return {"CANCELLED"}
		
		if resource_type == "GraphicsSpec":
			vehicle_name = main_collection.name
			vehicle_number = vehicle_name.replace("VEH", "").replace("HI", "").replace("LO", "").replace("TR", "").replace("GR", "").replace("MS", "")
			vehicle_number = vehicle_number.replace("veh", "").replace("hi", "").replace("lo", "").replace("tr", "").replace("gr", "").replace("ms", "").replace("_", "")
			
			try:
				test = int(vehicle_number)
			except:
				print("ERROR: main_collection's name is in the wrong format. Use something like VEH_122672_MS.")
			mGraphicsSpecId = int_to_id(vehicle_number)
			graphicsspec_collection = collections_types["GraphicsSpec"]
			
			collections = [graphicsspec_collection,]
			
			vehicle_dir = os.path.join(shared_vehicles_dir, vehicle_name)
			controlmesh_dir = os.path.join(vehicle_dir, "ControlMesh")
			skeleton_dir = os.path.join(vehicle_dir, "Skeleton")
			genesyinstance_dir = os.path.join(vehicle_dir, "GenesysInstance")
			graphicsspec_dir = os.path.join(vehicle_dir, "GraphicsSpec")
			graphicsspec_path = os.path.join(graphicsspec_dir, mGraphicsSpecId + ".dat")
			for file in os.listdir(graphicsspec_dir):
				if mGraphicsSpecId in file:
					graphicsspec_path = os.path.join(graphicsspec_dir, file)
					break
			
			if "Skeleton" in collections_types:
				pass
			else:
				_, _, _, mSkeletonId, _ = read_graphicsspec_hp(graphicsspec_path, resource_version)
				skeleton_path = os.path.join(skeleton_dir, mSkeletonId + ".dat")
				Skeleton = []
				if os.path.isfile(skeleton_path) == True:
					Skeleton = read_skeleton_hp(skeleton_path, resource_version)
				
				if len(Skeleton) > 0:
					skeleton_collection2 = bpy.data.collections.new(vehicle_number + "_Skeleton")
					skeleton_collection2["resource_type"] = "Skeleton"
					skeleton_collection2.color_tag = "COLOR_07"
					main_collection.children.link(skeleton_collection2)
					
					armature_created = False
					try:
						cm_armature_rig = bpy.context.scene.objects[mSkeletonId]
						armature_created = True
					except:
						cm_armature = bpy.data.armatures.new(mSkeletonId)
						cm_armature_rig = bpy.data.objects.new(mSkeletonId, cm_armature)
					
					skeleton_collection2.objects.link(cm_armature_rig)
					bpy.context.view_layer.objects.active = cm_armature_rig
					bpy.ops.object.mode_set(mode='EDIT', toggle=False)
					edit_bones = cm_armature_rig.data.edit_bones
					
					skeleton_method = "hinges"
					if skeleton_method == "joints":
						for i, sensor in enumerate(Skeleton):
							sensor_index, mSensorPosition, mSensorRotation, parent_sensor, older_sensor, child_sensor, has_ik, sensor_hash = sensor
							
							cm_bone_name = "Sensor_%03d" % sensor_index
							b = edit_bones.new(cm_bone_name)
							b.head = mSensorPosition
							#b.tail = mSensorPosition
							
							if parent_sensor != -1:
								b.parent = edit_bones["Sensor_%03d" % parent_sensor]
								b.use_connect = False
								#b.use_connect = True
								
								for sensor_ in Skeleton:
									if sensor_[0] == parent_sensor:
										#b.head = sensor_[1]
										b.tail = sensor_[1]
										break
							
							if b.length < 1e-3:
								b.tail = b.head + Vector([0.0, 0.0, 0.12])
								#b.head = b.tail + Vector([0.0, 0.0, 0.12])
							b["hash"] = int_to_id(sensor_hash)
							if has_ik == True:
								b["has_ik"] = has_ik
					
					elif skeleton_method == "hinges":
						for i, sensor in enumerate(Skeleton):
							sensor_index, mSensorPosition, mSensorRotation, parent_sensor, older_sensor, child_sensor, has_ik, sensor_hash = sensor
							
							cm_bone_name = "Sensor_%03d" % sensor_index
							b = edit_bones.new(cm_bone_name)
							b.head = mSensorPosition
							
							if parent_sensor != -1:
								b.parent = edit_bones["Sensor_%03d" % parent_sensor]
								b.use_connect = False
								#b.use_connect = True
								
								b.tail = Vector(mSensorPosition) + Vector([0.0, 0.2, 0.0])
								
								#for sensor_ in Skeleton:
								#	if sensor_[0] == parent_sensor:
								#		b.tail = Vector(mSensorPosition) + Vector([0.0, 0.2, 0.0])
								#		break
							
							if b.length < 1e-3:
								b.tail = b.head + Vector([0.0, 0.0, 0.12])
								#b.head = b.tail + Vector([0.0, 0.0, 0.12])
							b["hash"] = int_to_id(sensor_hash)
							if has_ik == True:
								b["has_ik"] = has_ik
					
					bpy.ops.object.mode_set(mode='OBJECT')
					mTransform = Matrix([[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]).transposed()
					cm_armature_rig.matrix_world = m @ mTransform
					if armature_created == False:
						cm_armature.display_type = 'WIRE'
						#cm_armature.show_names = True
						cm_armature.show_bone_custom_shapes = True
					cm_armature_rig.show_in_front = True
					
					# Bone shape
					try:
						bone_sphere = bpy.data.objects["dgi_sphere_skeleton"]
					except:
						bone_sphere = create_sphere(name="dgi_sphere_skeleton", radius=0.025)
						bone_sphere.use_fake_user = True
					
					for b in cm_armature_rig.pose.bones:
						b.custom_shape = bone_sphere
						b.use_custom_shape_bone_size = False
					
					#for renderable_object in renderable_objects:
					#	modifier = renderable_object.modifiers.new(name=mSkeletonId, type='ARMATURE')
					#	modifier.object = cm_armature_rig
			
			if "ControlMesh" in collections_types:
				pass
			else:
				_, _, _, _, mControlMeshId = read_graphicsspec_hp(graphicsspec_path, resource_version)
				controlmesh_path = os.path.join(controlmesh_dir, mControlMeshId + "_16.dat")
				ControlMeshes = []
				if os.path.isfile(controlmesh_path) == True:
					ControlMeshes = read_controlmesh(controlmesh_path)
				
				if len(ControlMeshes) > 0:
					controlmesh_collection = bpy.data.collections.new(vehicle_number + "_ControlMesh")
					controlmesh_collection["resource_type"] = "ControlMesh"
					controlmesh_collection.color_tag = "COLOR_08"
					main_collection.children.link(controlmesh_collection)
					
					armature_created = False
					try:
						cm_armature_rig = bpy.context.scene.objects[mControlMeshId]
						armature_created = True
					except:
						cm_armature = bpy.data.armatures.new(mControlMeshId)
						cm_armature_rig = bpy.data.objects.new(mControlMeshId, cm_armature)
					
					controlmesh_collection.objects.link(cm_armature_rig)
					bpy.context.view_layer.objects.active = cm_armature_rig
					bpy.ops.object.mode_set(mode='EDIT', toggle=False)
					edit_bones = cm_armature_rig.data.edit_bones
					
					for i, ControlMesh in enumerate(ControlMeshes):
						cm_index, cm_coordinates_A, cm_coordinates_B, cm_limit = ControlMesh
						#cm_bone_name = "ControlMesh_%03d.%03d" % (cm_index, vehicle_name)
						cm_bone_name = "Bone_%03d" % cm_index
						b = edit_bones.new(cm_bone_name)
						b.head = cm_coordinates_A
						b.tail = cm_coordinates_B
						
						if b.length < 1e-3:
							b.tail = b.head + Vector([0.0, 0.0, 0.12])
						
						b["Limit"] = cm_limit
					
					bpy.ops.object.mode_set(mode='OBJECT')	
					mTransform = Matrix([[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]).transposed()
					cm_armature_rig.matrix_world = m @ mTransform
					if armature_created == False:
						cm_armature.display_type = 'WIRE'
						#cm_armature.show_names = True
						cm_armature.show_bone_custom_shapes = True
					cm_armature_rig.show_in_front = True
					
					# Bone shape
					try:
						bone_sphere = bpy.data.objects["dgi_sphere_controlmesh"]
					except:
						bone_sphere = create_sphere(name="dgi_sphere_controlmesh", radius=0.025)
						bone_sphere.use_fake_user = True
					
					for b in cm_armature_rig.pose.bones:
						b.custom_shape = bone_sphere
						b.use_custom_shape_bone_size = False
					
					#for renderable_object in renderable_objects:
					#	modifier = renderable_object.modifiers.new(name=mControlMeshId, type='ARMATURE')
					#	modifier.object = cm_armature_rig
			
			if "Effects" in collections_types:
				pass
			elif "Effect" in collections_types:
				pass
			else:
				## Loading effects from vehicle file
				instances_effects = read_effects_graphicsspec_hp(graphicsspec_path, resource_version)
				
				# Creating effects object
				# Creating collection
				effects_collection = bpy.data.collections.new(vehicle_number + "_Effects")
				effects_collection["resource_type"] = "Effects"
				effects_collection.color_tag = "COLOR_05"
				main_collection.children.link(effects_collection)
				
				# Creating effect object
				for effect_instance in instances_effects:
					EffectId, i, effectsLocation, EffectData = effect_instance
					
					effect_object_name = "Effect_%d.%s" % (i, vehicle_number)
					effect_empty = bpy.data.objects.new(effect_object_name, None)
					effects_collection.objects.link(effect_empty)
					
					effect_empty['EffectId'] = EffectId
					#effect_empty['EffectData'] = EffectData
					
					effect_empty.matrix_world = m @ effect_empty.matrix_world
					
					for j, effectLocation in enumerate(effectsLocation):
						effect_object_name2 = "Effect_%d_copy_%d.%s" % (i, j, vehicle_number)
						effect_empty2 = bpy.data.objects.new(effect_object_name2, None)
						effect_empty2.parent = effect_empty
						
						mLocatorMatrix = Matrix([[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [*effectLocation[0], 1.0]]).transposed()
						effect_empty2.matrix_world = m @ mLocatorMatrix
						effect_empty2.rotation_mode = 'QUATERNION'
						effect_empty2.rotation_quaternion = [effectLocation[1][3], effectLocation[1][0], effectLocation[1][1], effectLocation[1][2]]
						
						effect_empty2.empty_display_type = 'SINGLE_ARROW'
						effect_empty2.empty_display_size = 0.5
						
						if EffectData != []:
							effect_empty2['sensor_hash'] = int_to_id(EffectData[j])
						
						effects_collection.objects.link(effect_empty2)
			
			if "Character" in collections_types:
				pass
			elif "Driver" in collections_types:
				pass
			else:
				genesysinstance_path = os.path.join(genesyinstance_dir, mGraphicsSpecId + ".dat")
				instances_character = read_genesysinstance_driver(genesyinstance_dir, genesysinstance_path, resource_version)
				
				## Creating driver object
				# Creating collection
				character_collection = bpy.data.collections.new(vehicle_number + "_Driver")
				character_collection["resource_type"] = "Character"
				character_collection.color_tag = "COLOR_06"
				main_collection.children.link(character_collection)
				
				# Creating driver object
				mCharacterSpecID, characterOffset = instances_character
				
				driver_object_name = "%s_Driver" % (vehicle_number)
				driver_empty = bpy.data.objects.new(driver_object_name, None)
				#driver_empty["CharacterSpecID"] = mCharacterSpecID
				character_collection.objects.link(driver_empty)
				
				if os.path.isfile(characterLibrary) == True:
					#if mCharacterSpecID == "":
					#	mCharacterSpecID = 30813
					
					with bpy.data.libraries.load(characterLibrary, link=False) as (data_from, data_to):
						data_to.collections = [col for col in data_from.collections if col.startswith(str(mCharacterSpecID))]
						if data_to.collections == []:
							data_to.collections = [[col for col in data_from.collections if col.endswith("Character")][0]]
					
					for library_collection in data_to.collections:
						driver_objects = library_collection.objects
						for driver_object in driver_objects:
							for child in driver_object.children:
								if child["renderable_index"] == 0:
									child.parent = driver_empty
									character_collection.objects.link(child)
									break
				
				mLocatorMatrix = Matrix([[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [*characterOffset, 1.0]]).transposed()
				
				driver_empty.matrix_world = m @ mLocatorMatrix
	
	return {'FINISHED'}


def read_genesysinstance_driver(genesyinstance_dir, genesysinstance_path, resource_version):
	instance_character = []
	with open(genesysinstance_path, "rb") as f:
		if resource_version == "NFSHPR_PC":
			f.seek(0x30, 0)
		elif resource_version == "NFSHP_PC":
			f.seek(0x20, 0)
		characterOffset = list(struct.unpack("<fff", f.read(0xC)))
		
		mCharacterSpecID = ""

		instance_character = [mCharacterSpecID, characterOffset]
	
	return instance_character


def read_effects_graphicsspec_hp(graphicsspec_path, resource_version):
	if resource_version == "NFSHPR_PC":
		data_format = ("<Q", 0x8)
		effect_data_length = 0x18
	elif resource_version == "NFSHP_PC":
		data_format = ("<I", 0x4)
		effect_data_length = 0xC
	
	instances = []
	instances_wheel = []
	instances_effects = []
	mControlMeshId = ""
	with open(graphicsspec_path, "rb") as f:
		if resource_version == "NFSHPR_PC":
			f.seek(0x30, 0)
		elif resource_version == "NFSHP_PC":
			f.seek(0x1C, 0)
		num_effects = struct.unpack("<I", f.read(0x4))[0]
		if resource_version == "NFSHPR_PC":
			unknown_0x34 = struct.unpack("<I", f.read(0x4))[0]		#new null
		mpEffectsId = struct.unpack(data_format[0], f.read(data_format[1]))[0]
		mpEffectsTable = struct.unpack(data_format[0], f.read(data_format[1]))[0]
		
		f.seek(mpEffectsId, 0)
		mEffectsId = struct.unpack("<%dI" % num_effects, f.read(0x4*num_effects))
		
		f.seek(mpEffectsTable, 0)
		for i in range(0, num_effects):
			f.seek(mpEffectsTable + effect_data_length*i, 0)
			effect_count = struct.unpack(data_format[0], f.read(data_format[1]))[0]
			effect_pointer = struct.unpack(data_format[0], f.read(data_format[1]))[0]
			unknown_pointer = struct.unpack(data_format[0], f.read(data_format[1]))[0]
			
			effectsLocation = []
			EffectData = []
			for j in range(0, effect_count):
				f.seek(effect_pointer + 0x20*j, 0)
				effectRotation = struct.unpack("<ffff", f.read(0x10))
				effectLocation = struct.unpack("<fff", f.read(0xC))
				padding = f.read(0x4)
				effectsLocation.append([effectLocation, effectRotation])
				
				if unknown_pointer != 0:
					f.seek(unknown_pointer + 0x4*j, 0)
					effect_data = struct.unpack("<I", f.read(0x4))[0]
					EffectData.append(effect_data)
			
			instances_effects.append([mEffectsId[i], i, effectsLocation[:], EffectData[:]])
	
	return instances_effects


def read_graphicsspec_mw(graphicsspec_path):
	instances = []
	instances_wheel = []
	instances_effects = []
	with open(graphicsspec_path, "rb") as f:
		mppModels = struct.unpack("<I", f.read(0x4))[0]
		null_0x4 = struct.unpack("<I", f.read(0x4))[0]
		null_0x8 = struct.unpack("<I", f.read(0x4))[0]
		mpWheelsData = struct.unpack("<I", f.read(0x4))[0]
		muPartsCount = struct.unpack("<H", f.read(0x2))[0]
		unknown_0x12 = struct.unpack("<B", f.read(0x1))[0]
		num_wheels = struct.unpack("<B", f.read(0x1))[0]
		num_behaviours = struct.unpack("<I", f.read(0x4))[0]
		mppBehaviour = struct.unpack("<I", f.read(0x4))[0]
		num_effects = struct.unpack("<I", f.read(0x4))[0]
		mpEffectsId = struct.unpack("<I", f.read(0x4))[0]
		mpEffectsTable = struct.unpack("<I", f.read(0x4))[0]
		padding = f.read(0x8)
		padding = f.read(0x10)
		
		f.seek(mpWheelsData, 0)
		mpWheelAllocateSpace = []
		mNumWheelParts = []
		object_placements = []
		wheel_transforms = []
		is_spinnables = []
		for i in range(0, num_wheels):
			mWheelOffset = list(struct.unpack("<4f", f.read(0x10)))
			mWheelRotation = struct.unpack("<4f", f.read(0x10))
			mWheelScale = struct.unpack("<4f", f.read(0x10))
			null = f.read(0x48)		# reserved for IDs
			mpWheelAllocateSpace.append(struct.unpack("<I", f.read(0x4))[0])
			spinnable_models = struct.unpack("<B", f.read(0x1))[0]
			padding = f.read(0x3)
			mNumWheelParts.append(struct.unpack("<B", f.read(0x1))[0])
			unknown_0x81 = struct.unpack("<B", f.read(0x1))[0]
			object_placement = f.read(0xE).split(b'\x00')[0]
			object_placement = str(object_placement, 'ascii').lower()
			object_placements.append(object_placement)
			
			wheel_transforms.append([mWheelOffset, mWheelRotation, mWheelScale])
			is_spinnables.append(bin(spinnable_models)[2:].zfill(0x8))
		
		first_wheel_pointer = min(mpWheelAllocateSpace)
		last_wheel_pointer = max(mpWheelAllocateSpace)
		last_wheel_index = mpWheelAllocateSpace.index(last_wheel_pointer)
		
		f.seek(mppBehaviour, 0)
		for i in range(0, num_behaviours):
			null_0x0 = struct.unpack("<I", f.read(0x4))[0]
			unknown_0x4 = struct.unpack("<I", f.read(0x4))[0]
			mBehaviourId = struct.unpack("<I", f.read(0x4))[0]
			unknown_0xC = struct.unpack("<I", f.read(0x4))[0]
			unknown_0x10 = struct.unpack("<I", f.read(0x4))[0]
		
		f.seek(mpEffectsId, 0)
		mEffectsId = struct.unpack("<%dI" % num_effects, f.read(0x4*num_effects))
		
		f.seek(mpEffectsTable, 0)
		for i in range(0, num_effects):
			f.seek(mpEffectsTable + 0xC*i, 0)
			effect_count = struct.unpack("<i", f.read(0x4))[0]
			effect_pointer = struct.unpack("<i", f.read(0x4))[0]
			unknown_pointer = struct.unpack("<i", f.read(0x4))[0]
			
			effectsLocation = []
			EffectData = []
			for j in range(0, effect_count):
				f.seek(effect_pointer + 0x20*j, 0)
				effectRotation = struct.unpack("<ffff", f.read(0x10))
				effectLocation = struct.unpack("<fff", f.read(0xC))
				padding = f.read(0x4)
				effectsLocation.append([effectLocation, effectRotation])
				
				if unknown_pointer != 0:
					f.seek(unknown_pointer + 0x4*j, 0)
					effect_data = struct.unpack("<I", f.read(0x4))[0]
					EffectData.append(effect_data)
			
			instances_effects.append([mEffectsId[i], i, effectsLocation[:], EffectData[:]])
		
		#mpResourceIds = first_wheel_pointer + sum(mNumWheelParts)*0x4
		mpResourceIds = last_wheel_pointer + mNumWheelParts[last_wheel_index]*0x4
		mpResourceIds += calculate_padding(mpResourceIds, 0x10)
		if mppModels >= first_wheel_pointer:
			mpResourceIds += muPartsCount*0x4
			mpResourceIds += calculate_padding(mpResourceIds, 0x10)
		
		f.seek(mpResourceIds, 0)
		mSkeletonId = bytes_to_id(f.read(0x4))
		_ = struct.unpack("<i", f.read(0x4))[0]
		muOffset = struct.unpack("<I", f.read(0x4))[0]
		padding = struct.unpack("<i", f.read(0x4))[0]
		if muOffset == 0x8:
			mPolygonSoupListId = mSkeletonId
			mSkeletonId = ""
			f.seek(-0x10, 1)
		elif muOffset > 0x8:
			mSkeletonId = ""
			f.seek(-0x10, 1)
		
		mPolygonSoupListId = bytes_to_id(f.read(0x4))
		_ = struct.unpack("<i", f.read(0x4))[0]
		muOffset = struct.unpack("<I", f.read(0x4))[0]
		padding = struct.unpack("<i", f.read(0x4))[0]
		if muOffset > 0x8:
			mPolygonSoupListId = ""
			f.seek(-0x10, 1)
		
		for i in range(0, muPartsCount):
			mModelId = bytes_to_id(f.read(0x4))
			_ = struct.unpack("<i", f.read(0x4))[0]
			muOffset = struct.unpack("<I", f.read(0x4))[0]
			padding = struct.unpack("<i", f.read(0x4))[0]

			instances.append([mModelId])
		
		f.seek(-0x10 * sum(mNumWheelParts), 2)
		for i in range(0, num_wheels):
			for j in range(0, mNumWheelParts[i]):
				mModelId = bytes_to_id(f.read(0x4))
				_ = struct.unpack("<i", f.read(0x4))[0]
				muOffset = struct.unpack("<I", f.read(0x4))[0]
				padding = struct.unpack("<i", f.read(0x4))[0]
				
				is_spinnable = bool(int(is_spinnables[i][-1-j]))
				placement = object_placements[i]
				
				instances_wheel.append([mModelId, [placement, is_spinnable, wheel_transforms[i]]])
	
	return (instances, instances_wheel, instances_effects, mSkeletonId, mPolygonSoupListId)


def read_graphicsspec_hp(graphicsspec_path, resource_version):
	if resource_version == "NFSHPR_PC":
		data_format = ("<Q", 0x8)
		effect_data_length = 0x18
	elif resource_version == "NFSHP_PC":
		data_format = ("<I", 0x4)
		effect_data_length = 0xC
	
	instances = []
	instances_wheel = []
	instances_effects = []
	mControlMeshId = ""
	with open(graphicsspec_path, "rb") as f:
		mppModels = struct.unpack(data_format[0], f.read(data_format[1]))[0]
		null_0x8 = struct.unpack(data_format[0], f.read(data_format[1]))[0]
		null_0x10 = struct.unpack(data_format[0], f.read(data_format[1]))[0]
		mpWheelsData = struct.unpack(data_format[0], f.read(data_format[1]))[0]
		muPartsCount = struct.unpack("<H", f.read(0x2))[0]
		unknown_0x12 = struct.unpack("<B", f.read(0x1))[0]
		num_wheels = struct.unpack("<B", f.read(0x1))[0]
		num_behaviours = struct.unpack("<I", f.read(0x4))[0]
		mppBehaviour = struct.unpack(data_format[0], f.read(data_format[1]))[0]
		num_effects = struct.unpack("<I", f.read(0x4))[0]
		if resource_version == "NFSHPR_PC":
			unknown_0x34 = struct.unpack("<I", f.read(0x4))[0]		#new null
		mpEffectsId = struct.unpack(data_format[0], f.read(data_format[1]))[0]
		mpEffectsTable = struct.unpack(data_format[0], f.read(data_format[1]))[0]
		padding = f.read(0x8)
		padding = f.read(0x10)
		
		f.seek(mpWheelsData, 0)
		mpWheelAllocateSpace = []
		mNumWheelParts = []
		object_placements = []
		wheel_transforms = []
		is_spinnables = []
		for i in range(0, num_wheels):
			mpWheelAllocateSpace.append(struct.unpack(data_format[0], f.read(data_format[1]))[0])
			spinnable_models = struct.unpack("<I", f.read(0x4))[0]			
			mNumWheelParts.append(struct.unpack("<H", f.read(0x2))[0])
			padding = f.read(0x2)
			object_placement = f.read(0x10).split(b'\x00')[0]
			object_placement = str(object_placement, 'ascii').lower()
			object_placements.append(object_placement)
			if resource_version == "NFSHPR_PC":
				null = f.read(0x10)
			elif resource_version == "NFSHP_PC":
				null = f.read(0x4)
			mWheelOffset = list(struct.unpack("<4f", f.read(0x10)))
			mWheelRotation = struct.unpack("<4f", f.read(0x10))
			mWheelScale = struct.unpack("<4f", f.read(0x10))
			
			
			wheel_transforms.append([mWheelOffset, mWheelRotation, mWheelScale])
			is_spinnables.append(bin(spinnable_models)[2:].zfill(0x8))
		
		first_wheel_pointer = min(mpWheelAllocateSpace)
		last_wheel_pointer = max(mpWheelAllocateSpace)
		last_wheel_index = mpWheelAllocateSpace.index(last_wheel_pointer)
		
		f.seek(mppBehaviour, 0)
		for i in range(0, num_behaviours):
			null_0x0 = struct.unpack(data_format[0], f.read(data_format[1]))[0]
			unknown_0x8 = struct.unpack(data_format[0], f.read(data_format[1]))[0]
			mBehaviourId = struct.unpack("<I", f.read(0x4))[0]
			unknown_0x14 = struct.unpack("<I", f.read(0x4))[0]
			unknown_0x18 = struct.unpack("<I", f.read(0x4))[0]
			if resource_version == "NFSHPR_PC":
				padding = struct.unpack("<I", f.read(0x4))[0]
		
		f.seek(mpEffectsId, 0)
		mEffectsId = struct.unpack("<%dI" % num_effects, f.read(0x4*num_effects))
		
		f.seek(mpEffectsTable, 0)
		for i in range(0, num_effects):
			f.seek(mpEffectsTable + effect_data_length*i, 0)
			effect_count = struct.unpack(data_format[0], f.read(data_format[1]))[0]
			effect_pointer = struct.unpack(data_format[0], f.read(data_format[1]))[0]
			unknown_pointer = struct.unpack(data_format[0], f.read(data_format[1]))[0]
			
			effectsLocation = []
			EffectData = []
			for j in range(0, effect_count):
				f.seek(effect_pointer + 0x20*j, 0)
				effectRotation = struct.unpack("<ffff", f.read(0x10))
				effectLocation = struct.unpack("<fff", f.read(0xC))
				padding = f.read(0x4)
				effectsLocation.append([effectLocation, effectRotation])
				
				if unknown_pointer != 0:
					f.seek(unknown_pointer + 0x4*j, 0)
					effect_data = struct.unpack("<I", f.read(0x4))[0]
					EffectData.append(effect_data)
			
			instances_effects.append([mEffectsId[i], i, effectsLocation[:], EffectData[:]])
		
		#mpResourceIds = first_wheel_pointer + sum(mNumWheelParts)*0x4
		mpResourceIds = last_wheel_pointer + mNumWheelParts[last_wheel_index]*data_format[1]
		mpResourceIds += calculate_padding(mpResourceIds, 0x10)
		if mppModels >= first_wheel_pointer:
			mpResourceIds += muPartsCount*data_format[1]
			mpResourceIds += calculate_padding(mpResourceIds, 0x10)
		
		f.seek(mpResourceIds, 0)
		mSkeletonId = bytes_to_id(f.read(0x4))
		_ = struct.unpack("<i", f.read(0x4))[0]
		muOffset = struct.unpack("<I", f.read(0x4))[0]
		padding = struct.unpack("<i", f.read(0x4))[0]
		if (muOffset == 0x10 and resource_version == "NFSHPR_PC") or (muOffset == 0x8 and resource_version == "NFSHP_PC"):
			#mControlMeshId = mSkeletonId
			mControlMeshId = mSkeletonId
			mSkeletonId = ""
			f.seek(-0x10, 1)
		elif muOffset > 0x10:
			mSkeletonId = ""
			f.seek(-0x10, 1)
		
		mControlMeshId = bytes_to_id(f.read(0x4))
		_ = struct.unpack("<i", f.read(0x4))[0]
		muOffset = struct.unpack("<I", f.read(0x4))[0]
		padding = struct.unpack("<i", f.read(0x4))[0]
		if muOffset > 0x10:
			mControlMeshId = ""
			f.seek(-0x10, 1)
		
		for i in range(0, muPartsCount):
			mModelId = bytes_to_id(f.read(0x4))
			_ = struct.unpack("<i", f.read(0x4))[0]
			muOffset = struct.unpack("<I", f.read(0x4))[0]
			padding = struct.unpack("<i", f.read(0x4))[0]

			instances.append([mModelId])
		
		f.seek(-0x10 * sum(mNumWheelParts), 2)
		for i in range(0, num_wheels):
			for j in range(0, mNumWheelParts[i]):
				mModelId = bytes_to_id(f.read(0x4))
				_ = struct.unpack("<i", f.read(0x4))[0]
				muOffset = struct.unpack("<I", f.read(0x4))[0]
				padding = struct.unpack("<i", f.read(0x4))[0]
				
				is_spinnable = bool(int(is_spinnables[i][-1-j]))
				placement = object_placements[i]
				
				instances_wheel.append([mModelId, [placement, is_spinnable, wheel_transforms[i]]])
	
	return (instances, instances_wheel, instances_effects, mSkeletonId, mControlMeshId)


def read_skeleton_mw(skeleton_path):
	Skeleton = []
	with open(skeleton_path, "rb") as f:
		unk = struct.unpack("<H", f.read(0x2))[0]
		muCount = struct.unpack("<H", f.read(0x2))[0]
		mppPointer = struct.unpack("<I", f.read(0x4))[0]
		mppPointer2 = struct.unpack("<I", f.read(0x4))[0]
		mppPointer3 = struct.unpack("<I", f.read(0x4))[0]
		miNumberOfIKParts = struct.unpack("<H", f.read(0x2))[0]
		
		miIkParts = []
		if miNumberOfIKParts != 0:
			f.seek(mppPointer2, 0)
			for i in range(0, miNumberOfIKParts):
				miIkPartIndex = struct.unpack("<i", f.read(0x4))[0]
				miIkParts.append(miIkPartIndex)
		
		f.seek(mppPointer, 0)
		for i in range(0, muCount):
			f.seek(mppPointer + 0x30*i, 0)
			location = struct.unpack("<fff", f.read(0xC))
			padding = f.read(0x4)
			rotation = struct.unpack("<ffff", f.read(0x10))
			parent_sensor = struct.unpack("<i", f.read(0x4))[0]
			older_sensor = struct.unpack("<i", f.read(0x4))[0]
			child_sensor = struct.unpack("<i", f.read(0x4))[0]
			sensor_index = struct.unpack("<i", f.read(0x4))[0]
			
			has_ik = sensor_index in miIkParts
			
			Skeleton.append([sensor_index, location, rotation, parent_sensor, older_sensor, child_sensor, has_ik])
		
		f.seek(mppPointer3, 0)
		for i in range(0, muCount):
			hash = struct.unpack("<I", f.read(0x4))[0]
			Skeleton[i].append(hash)
	
	return Skeleton


def read_skeleton_hp(skeleton_path, resource_version):
	if resource_version == "NFSHPR_PC":
		data_format = ("<Q", 0x8)
	elif resource_version == "NFSHP_PC":
		data_format = ("<I", 0x4)
	
	Skeleton = []
	with open(skeleton_path, "rb") as f:
		mppPointer = struct.unpack(data_format[0], f.read(data_format[1]))[0]
		mppPointer2 = struct.unpack(data_format[0], f.read(data_format[1]))[0]
		mppPointer3 = struct.unpack(data_format[0], f.read(data_format[1]))[0]
		muCount = struct.unpack(data_format[0], f.read(data_format[1]))[0]
		
		f.seek(mppPointer, 0)
		for i in range(0, muCount):
			f.seek(mppPointer + 0x20*i, 0)
			location = struct.unpack("<fff", f.read(0xC))
			padding = f.read(0x4)
			rotation = []
			parent_sensor = struct.unpack("<i", f.read(0x4))[0]
			older_sensor = struct.unpack("<i", f.read(0x4))[0]
			child_sensor = struct.unpack("<i", f.read(0x4))[0]
			sensor_index = struct.unpack("<i", f.read(0x4))[0]
			
			has_ik = False
			
			Skeleton.append([sensor_index, location, rotation, parent_sensor, older_sensor, child_sensor, has_ik])
		
		f.seek(mppPointer3, 0)
		for i in range(0, muCount):
			hash = struct.unpack("<I", f.read(0x4))[0]
			Skeleton[i].append(hash)
	
	return Skeleton


def read_controlmesh(controlmesh_path):
	ControlMeshes = []
	with open(controlmesh_path, "rb") as f:
		unknown_0x0 = struct.unpack("<I", f.read(0x4))[0]
		size = struct.unpack("<I", f.read(0x4))[0]
		
		f.seek(0x10, 0)
		for i in range(0, 0x40):
			cm_coordinates_A = struct.unpack("<fff", f.read(0xC))
			w = struct.unpack("<f", f.read(0x4))[0]
			
			ControlMeshes.append([i, cm_coordinates_A])
		
		for i in range(0, 0x40):
			cm_coordinates_B = struct.unpack("<fff", f.read(0xC))
			w = struct.unpack("<f", f.read(0x4))[0]
			
			ControlMeshes[i].append(cm_coordinates_B)
		
		for i in range(0, 0x40):
			cm_limit = struct.unpack("<ffff", f.read(0x10))
			
			ControlMeshes[i].append(cm_limit[0])
			
			if len(set(cm_limit)) != 1:
				print("DEBUG: different limits found in ControlMesh file.")
				print(cm_limit)
		
	return ControlMeshes


def read_shader(shader_path):
	ShaderType = ""
	raster_types = []
	with open(shader_path, "rb") as f:
		file_size = os.path.getsize(shader_path)
		material_state_info_pointer = struct.unpack("<i", f.read(0x4))[0]
		num_material_states = struct.unpack("<B", f.read(0x1))[0]
		
		f.seek(0x8, 0)
		shader_description_offset = struct.unpack("<i", f.read(0x4))[0]
		f.seek(shader_description_offset, 0)
		shader_description = f.read(file_size-shader_description_offset).split(b'\x00')[0]
		shader_description = str(shader_description, 'ascii')
		
		# Material constants
		material_constants = []
		f.seek(material_state_info_pointer, 0)
		for i in range(0, num_material_states):
			f.seek(material_state_info_pointer + 0x3C*i + 0x32, 0)
			material_constants.append(struct.unpack("<H", f.read(0x2))[0])
		
		# VertexShader
		f.seek(0x50, 0)
		muNumVertexShaderConstantsInstances = struct.unpack("<B", f.read(0x1))[0]
		
		
		# PixelShader
		f.seek(0x53, 0)
		muNumPixelShaderConstantsInstances = struct.unpack("<B", f.read(0x1))[0]
		
		
		f.seek(0x10, 0)
		mpauShaderConstantsInstanceSize = struct.unpack("<I", f.read(0x4))[0]
		mpafShaderConstantsInstanceData = struct.unpack("<I", f.read(0x4))[0]
		mpauShaderNamesHash = struct.unpack("<I", f.read(0x4))[0]
		
		f.seek(mpauShaderConstantsInstanceSize, 0)
		mauVertexShaderConstantsInstanceSize = struct.unpack("<%dB" % muNumVertexShaderConstantsInstances, f.read(0x1*muNumVertexShaderConstantsInstances))
		mauPixelShaderConstantsInstanceSize = struct.unpack("<%dB" % muNumPixelShaderConstantsInstances, f.read(0x1*muNumPixelShaderConstantsInstances))
		
		f.seek(mpafShaderConstantsInstanceData, 0)
		mafVertexShaderConstantsInstanceData = []
		mafPixelShaderConstantsInstanceData = []
		for i in range(0, muNumVertexShaderConstantsInstances):
			mafVertexShaderConstantsInstanceData.append(struct.unpack("<ffff", f.read(0x4*4)))
		for i in range(0, muNumPixelShaderConstantsInstances):
			mafPixelShaderConstantsInstanceData.append(struct.unpack("<ffff", f.read(0x4*4)))
		
		f.seek(mpauShaderNamesHash, 0)
		mauVertexShaderNamesHash = struct.unpack("<%di" % muNumVertexShaderConstantsInstances, f.read(0x4*muNumVertexShaderConstantsInstances))
		mauPixelShaderNamesHash = struct.unpack("<%di" % muNumPixelShaderConstantsInstances, f.read(0x4*muNumPixelShaderConstantsInstances))
		
		
		# Samplers
		f.seek(0x5C, 0)
		mpaSamplers = struct.unpack("<i", f.read(0x4))[0]
		miNumSamplers = struct.unpack("<B", f.read(0x1))[0]
		
		f.seek(0x68, 0)
		end_raster_types_offset = struct.unpack("<i", f.read(0x4))[0]
		
		raster_type_offsets = []
		miChannel = []
		for i in range(0, miNumSamplers):
			f.seek(mpaSamplers + i*0x8, 0)
			raster_type_offsets.append(struct.unpack("<i", f.read(0x4))[0])
			miChannel.append(struct.unpack("<B", f.read(0x1))[0])
		
		raster_type_offsets.append(end_raster_types_offset)
		for i in range(0, miNumSamplers):
			f.seek(raster_type_offsets[i], 0)
			if raster_type_offsets[i] > raster_type_offsets[i+1]:
				raster_type = f.read(end_raster_types_offset-raster_type_offsets[i]).split(b'\x00')[0]
			else:
				raster_type = f.read(raster_type_offsets[i+1]-raster_type_offsets[i]).split(b'\x00')[0]
			raster_type = str(raster_type, 'ascii')
			
			#if miChannel[i] == 15:
			#	continue
			#elif miChannel[i] == 13:
			#	continue
			raster_types.append([miChannel[i], raster_type])
		
		if shader_description == "Road_Night_Detailmap_Opaque_Singlesided":
			#This shader is missing the definition of two AoMaps
			raster_types.append([3, "AoMapSampler"])
			raster_types.append([4, "AoMapSampler2"])
		
		elif shader_description == "Tunnel_Road_Detailmap_Opaque_Singlesided":
			#This shader is missing the definition of two AoMaps
			raster_types.append([3, "AoMapSampler"])
			raster_types.append([4, "AoMapSampler2"])
		
		elif shader_description == "Cable_GreyScale_Doublesided":
			# This shader is used by a material (3A_47_5B_86) that has a different number of parameters 1
			# than the specified by the shader
			muNumVertexShaderConstantsInstances = 2
		
		#elif shader_description == "Vehicle_Greyscale_Window_Textured":
		#	#This shader has one extra map definition
		#	raster_types.remove([14, "GlassFractureSampler"])
		
		raster_types.sort(key=lambda x:x[0])
		
		#raster_types_splitted = []
		#for raster_type_data in raster_types:
		#	raster_types_splitted.append(raster_type_data[1])
		#
		#raster_types = raster_types_splitted[:]
		
		raster_types_dict = {}
		for raster_type_data in raster_types:
			raster_types_dict[raster_type_data[0]] = raster_type_data[1]
	
	return (shader_description, raster_types_dict, num_material_states, material_constants, muNumVertexShaderConstantsInstances, mafVertexShaderConstantsInstanceData, mauVertexShaderNamesHash, muNumPixelShaderConstantsInstances, mafPixelShaderConstantsInstanceData, mauPixelShaderNamesHash)


def read_shader_mw(shader_path):
	ShaderType = ""
	raster_types = []
	with open(shader_path, "rb") as f:
		file_size = os.path.getsize(shader_path)
		
		# Shader description
		f.seek(0x8, 0)
		shader_description_offset = struct.unpack("<i", f.read(0x4))[0]
		f.seek(0x10, 0)
		end_sampler_types_offset = struct.unpack("<H", f.read(0x2))[0]
		resources_pointer = struct.unpack("<H", f.read(0x2))[0]
		f.seek(shader_description_offset, 0)
		shader_description = f.read(resources_pointer-shader_description_offset).split(b'\x00')[0]
		shader_description = str(shader_description, 'ascii')
		
		# Shader parameters
		f.seek(0x14, 0)
		shader_parameters_indices_pointer = struct.unpack("<i", f.read(0x4))[0]
		shader_parameters_ones_pointer = struct.unpack("<i", f.read(0x4))[0]
		shader_parameters_nameshash_pointer = struct.unpack("<i", f.read(0x4))[0]
		shader_parameters_data_pointer = struct.unpack("<i", f.read(0x4))[0]
		num_shader_parameters = struct.unpack("<B", f.read(0x1))[0]
		num_shader_parameters_withdata = struct.unpack("<B", f.read(0x1))[0]
		f.seek(0x2, 1)
		shader_parameters_names_pointer = struct.unpack("<i", f.read(0x4))[0]
		shader_parameters_end_pointer = struct.unpack("<i", f.read(0x4))[0]
		if shader_parameters_end_pointer == 0:
			shader_parameters_end_pointer = end_sampler_types_offset
		
		f.seek(shader_parameters_indices_pointer, 0)
		shader_parameters_Indices = list(struct.unpack("<%db" % num_shader_parameters, f.read(0x1*num_shader_parameters)))
		
		f.seek(shader_parameters_ones_pointer, 0)
		shader_parameters_Ones = list(struct.unpack("<%db" % num_shader_parameters, f.read(0x1*num_shader_parameters)))
		
		f.seek(shader_parameters_nameshash_pointer, 0)
		shader_parameters_NamesHash = list(struct.unpack("<%dI" % num_shader_parameters, f.read(0x4*num_shader_parameters)))
		
		f.seek(shader_parameters_data_pointer, 0)
		shader_parameters_Data = []
		# for i in range(0, num_shader_parameters):
			# if shader_parameters_Indices[i] == -1:
				# shader_parameters_Data.append(None)
			# else:
				# shader_parameters_Data.append(struct.unpack("<4f", f.read(0x10)))
		
		for i in range(0, num_shader_parameters):
			if shader_parameters_Indices[i] == -1:
				shader_parameters_Data.append(None)
			else:
				f.seek(shader_parameters_data_pointer + 0x10*shader_parameters_Indices[i], 0)
				shader_parameters_Data.append(struct.unpack("<4f", f.read(0x10)))
				#parameters_names.append(shader_parameters_Names[i])
		
		shader_parameters_Names = []
		#shader_parameters_Names = [""]*num_shader_parameters
		for i in range(0, num_shader_parameters):
			f.seek(shader_parameters_names_pointer + i*0x4, 0)
			pointer = struct.unpack("<i", f.read(0x4))[0]
			f.seek(pointer, 0)
			parameter_name = f.read(shader_parameters_end_pointer-pointer).split(b'\x00')[0]
			parameter_name = str(parameter_name, 'ascii')
			shader_parameters_Names.append(parameter_name)
			#shader_parameters_Names[shader_parameters_Indices[i]] = parameter_name
		
		shader_parameters = [shader_parameters_Indices, shader_parameters_Ones, shader_parameters_NamesHash, shader_parameters_Data, shader_parameters_Names]
		
		# Samplers and material constants
		f.seek(0x5C, 0)
		miNumSamplers = struct.unpack("<B", f.read(0x1))[0]
		f.seek(0x3, 1)
		mpaMaterialConstants = struct.unpack("<i", f.read(0x4))[0]
		mpaSamplersChannel = struct.unpack("<i", f.read(0x4))[0]
		mpaSamplers = struct.unpack("<i", f.read(0x4))[0]
		f.seek(0x80, 0)
		end_raster_types_offset = struct.unpack("<i", f.read(0x4))[0]
		if end_raster_types_offset == 0:
			end_raster_types_offset = end_sampler_types_offset
		
		f.seek(mpaMaterialConstants, 0)
		material_constants = struct.unpack("<%dH" % miNumSamplers, f.read(0x2*miNumSamplers))
		
		f.seek(mpaSamplersChannel, 0)
		miChannel = struct.unpack("<%dB" % miNumSamplers, f.read(0x1*miNumSamplers))
		
		f.seek(mpaSamplers, 0)
		raster_type_offsets = list(struct.unpack("<%di" % miNumSamplers, f.read(0x4*miNumSamplers)))
		raster_type_offsets.append(end_raster_types_offset)
		
		for i in range(0, miNumSamplers):
			f.seek(raster_type_offsets[i], 0)
			if raster_type_offsets[i] > raster_type_offsets[i+1]:
				raster_type = f.read(end_raster_types_offset-raster_type_offsets[i]).split(b'\x00')[0]
			else:
				raster_type = f.read(raster_type_offsets[i+1]-raster_type_offsets[i]).split(b'\x00')[0]
			raster_type = str(raster_type, 'ascii')
			raster_types.append([miChannel[i], raster_type])
		
		raster_types.sort(key=lambda x:x[0])
		
		raster_types_dict = {}
		for raster_type_data in raster_types:
			raster_types_dict[raster_type_data[0]] = raster_type_data[1]
		
		# VertexDescriptor
		f.seek(resources_pointer, 0)
		mVertexDescriptorId = bytes_to_id(f.read(0x4))
	
	return (shader_description, mVertexDescriptorId, miNumSamplers, raster_types_dict, shader_parameters, material_constants)


def read_shader_hp(shader_path, resource_version):
	if resource_version == "NFSHPR_PC":
		data_format = ("<Q", 0x8)
	elif resource_version == "NFSHP_PC":
		data_format = ("<I", 0x4)
	
	ShaderType = ""
	raster_types = []
	texture_samplers = []
	with open(shader_path, "rb") as f:
		file_size = os.path.getsize(shader_path)
		
		# Shader description
		pointer_0 = struct.unpack(data_format[0], f.read(data_format[1]))[0]
		pointer_1 = struct.unpack(data_format[0], f.read(data_format[1]))[0]
		shader_description_offset = struct.unpack(data_format[0], f.read(data_format[1]))[0]
		f.seek(0x4, 1)
		end_sampler_types_offset = struct.unpack("<H", f.read(0x2))[0]
		resources_pointer = struct.unpack("<H", f.read(0x2))[0]
		shader_parameters_pointers = f.tell()
		f.seek(shader_description_offset, 0)
		shader_description = f.read(resources_pointer-shader_description_offset).split(b'\x00')[0]
		shader_description = str(shader_description, 'ascii')
		
		# Shader parameters
		f.seek(shader_parameters_pointers, 0)
		shader_parameters_indices_pointer = struct.unpack(data_format[0], f.read(data_format[1]))[0]
		shader_parameters_ones_pointer = struct.unpack(data_format[0], f.read(data_format[1]))[0]
		shader_parameters_nameshash_pointer = struct.unpack(data_format[0], f.read(data_format[1]))[0]
		shader_parameters_data_pointer = struct.unpack(data_format[0], f.read(data_format[1]))[0]
		num_shader_parameters = struct.unpack("<B", f.read(0x1))[0]
		num_shader_parameters_withdata = struct.unpack("<B", f.read(0x1))[0]
		f.seek(0x2, 1)
		if resource_version == "NFSHPR_PC":
			f.seek(0x4, 1)
		shader_parameters_names_pointer = struct.unpack(data_format[0], f.read(data_format[1]))[0]
		shader_parameters_end_pointer = struct.unpack(data_format[0], f.read(data_format[1]))[0]
		if shader_parameters_end_pointer == 0:
			shader_parameters_end_pointer = end_sampler_types_offset
		
		f.seek(shader_parameters_indices_pointer, 0)
		shader_parameters_Indices = list(struct.unpack("<%db" % num_shader_parameters, f.read(0x1*num_shader_parameters)))
		
		f.seek(shader_parameters_ones_pointer, 0)
		shader_parameters_Ones = list(struct.unpack("<%db" % num_shader_parameters, f.read(0x1*num_shader_parameters)))
		
		f.seek(shader_parameters_nameshash_pointer, 0)
		shader_parameters_NamesHash = list(struct.unpack("<%dI" % num_shader_parameters, f.read(0x4*num_shader_parameters)))
		
		f.seek(shader_parameters_data_pointer, 0)
		shader_parameters_Data = []
		# for i in range(0, num_shader_parameters):
			# if shader_parameters_Indices[i] == -1:
				# shader_parameters_Data.append(None)
			# else:
				# shader_parameters_Data.append(struct.unpack("<4f", f.read(0x10)))
		
		for i in range(0, num_shader_parameters):
			if shader_parameters_Indices[i] == -1:
				shader_parameters_Data.append(None)
			else:
				f.seek(shader_parameters_data_pointer + 0x10*shader_parameters_Indices[i], 0)
				shader_parameters_Data.append(struct.unpack("<4f", f.read(0x10)))
				#parameters_names.append(shader_parameters_Names[i])
		
		shader_parameters_Names = []
		#shader_parameters_Names = [""]*num_shader_parameters
		for i in range(0, num_shader_parameters):
			f.seek(shader_parameters_names_pointer + i*data_format[1], 0)
			pointer = struct.unpack(data_format[0], f.read(data_format[1]))[0]
			f.seek(pointer, 0)
			parameter_name = f.read(shader_parameters_end_pointer-pointer).split(b'\x00')[0]
			parameter_name = str(parameter_name, 'ascii')
			shader_parameters_Names.append(parameter_name)
			#shader_parameters_Names[shader_parameters_Indices[i]] = parameter_name
		
		shader_parameters = [shader_parameters_Indices, shader_parameters_Ones, shader_parameters_NamesHash, shader_parameters_Data, shader_parameters_Names]
		
		# Samplers and material constants
		if resource_version == "NFSHPR_PC":
			f.seek(0xB0, 0)
		elif resource_version == "NFSHP_PC":
			f.seek(0x5C, 0)
		miNumSamplers = struct.unpack("<B", f.read(0x1))[0]
		f.seek(0x3, 1)
		if resource_version == "NFSHPR_PC":
			f.seek(0x4, 1)
		mpaMaterialConstants = struct.unpack(data_format[0], f.read(data_format[1]))[0]
		mpaSamplersChannel = struct.unpack(data_format[0], f.read(data_format[1]))[0]
		mpaSamplers = struct.unpack(data_format[0], f.read(data_format[1]))[0]
		if resource_version == "NFSHPR_PC":
			f.seek(0xF8, 0)
		elif resource_version == "NFSHP_PC":
			f.seek(0x80, 0)
		end_raster_types_offset = struct.unpack("<i", f.read(0x4))[0]
		if end_raster_types_offset == 0:
			end_raster_types_offset = end_sampler_types_offset
		
		f.seek(mpaMaterialConstants, 0)
		material_constants = struct.unpack("<%dH" % miNumSamplers, f.read(0x2*miNumSamplers))
		
		f.seek(mpaSamplersChannel, 0)
		miChannel = struct.unpack("<%dB" % miNumSamplers, f.read(0x1*miNumSamplers))
		
		f.seek(mpaSamplers, 0)
		if resource_version == "NFSHPR_PC":
			raster_type_offsets = list(struct.unpack("<%dQ" % miNumSamplers, f.read(0x8*miNumSamplers)))
		elif resource_version == "NFSHP_PC":
			raster_type_offsets = list(struct.unpack("<%dI" % miNumSamplers, f.read(0x4*miNumSamplers)))
		raster_type_offsets.append(end_raster_types_offset)
		
		for i in range(0, miNumSamplers):
			f.seek(raster_type_offsets[i], 0)
			if raster_type_offsets[i] > raster_type_offsets[i+1]:
				raster_type = f.read(end_raster_types_offset-raster_type_offsets[i]).split(b'\x00')[0]
			else:
				raster_type = f.read(raster_type_offsets[i+1]-raster_type_offsets[i]).split(b'\x00')[0]
			raster_type = str(raster_type, 'ascii')
			raster_types.append([miChannel[i], raster_type])
			texture_samplers.append(raster_type)
		
		raster_types.sort(key=lambda x:x[0])
		
		raster_types_dict = {}
		for raster_type_data in raster_types:
			raster_types_dict[raster_type_data[0]] = raster_type_data[1]
		
		if shader_description == "DEBUG_TRIGGER_Illuminance_Greyscale_Singlesided":
			texture_samplers.insert(-1, "IlluminanceTextureSampler")
		
		# VertexDescriptor
		f.seek(resources_pointer, 0)
		mVertexDescriptorId = bytes_to_id(f.read(0x4))
	
	return (shader_description, mVertexDescriptorId, miNumSamplers, raster_types_dict, shader_parameters, material_constants)


def get_mShaderID(shader_description, resource_type):
	shaders = {	'VideoWall_Diffuse_Opaque_Singlesided': '19_6E_C7_0F',
				'Chevron_Illuminated_Greyscale_Singlesided': '1A_06_FF_0F',
				'Tunnel_DriveableSurface_Detailmap_Opaque_Singlesided': '1B_D8_B8_27',
				'Cruciform_1Bit_Doublesided_Instanced': '1F_DA_DF_6E',
				'Vehicle_Opaque_BodypartsSkin_EnvMapped': '21_6D_2C_08',
				'Vehicle_1Bit_Tyre_Textured': '2D_40_9E_05',
				'Vehicle_Livery_Alpha_CarGuts': '31_8E_3B_9E',
				'Vehicle_Greyscale_Window_Textured': '33_0B_A4_5E',
				'Vehicle_Greyscale_Headlight_Doublesided': '34_11_6F_C8',
				'BuildingGlass_Transparent_Doublesided': '35_91_5B_CA',
				'Diffuse_Greyscale_Singlesided': '36_9A_6B_40',
				'Diffuse_Opaque_Singlesided': '37_C2_9A_C3',
				'Cruciform_1Bit_Doublesided': '37_E7_77_6B',
				'Diffuse_1Bit_Doublesided': '3C_A3_99_3E',
				'Tunnel_Lightmapped_1Bit_Doublesided2': '3D_C9_A3_7B',
				'Gold_Illuminated_Reflective_Opaque_Singlesided': '3F_28_A4_93',
				'Diffuse_Greyscale_Doublesided': '42_73_1A_D2',
				'Sign_Illuminance_Diffuse_Opaque_Singlesided': '46_FB_C2_67',
				'Tint_Specular_1Bit_Doublesided': '49_3C_26_F6',
				'Sign_Diffuse_Opaque_Singlesided': '49_A7_17_A0',
				'Specular_Opaque_Singlesided': '4B_D9_70_EA',
				'Grass_Specular_Opaque_Singlesided': '4D_7F_80_14',
				'Tint_Building_Opaque_Singlesided': '4E_83_F2_D0',
				'Vehicle_GreyScale_Decal_Textured_UVAnim': '51_80_C9_2F',
				'Vehicle_Livery_Alpha_CarGuts_Skin': '56_60_98_39',
				'Building_Opaque_Singlesided': '57_0B_99_65',
				'Vehicle_Opaque_Decal_Textured_EnvMapped_PoliceLights': '5D_1F_A9_50',
				'Tunnel_Road_Detailmap_Opaque_Singlesided': '5D_C3_BE_4F',
				'Tunnel_Lightmapped_1Bit_Singlesided2': '65_25_EA_21',
				'Vehicle_Opaque_CarbonFibre_Textured': '66_30_78_11',
				'ShoreLine_Diffuse_Greyscale_Singlesided': '66_63_5A_26',
				'Specular_Greyscale_Singlesided': '6B_A8_27_CA',
				'Vehicle_Opaque_Metal_Textured_Skin': '6F_53_CC_FA',
				'Terrain_Diffuse_Opaque_Singlesided': '71_12_EC_98',
				'Water_Specular_Opaque_Singlesided': '73_B0_DA_EC',
				'Vehicle_Opaque_PlasticMatt_Textured': '78_CE_40_2C',
				'Vehicle_Opaque_WheelChrome_Textured_Illuminance': '79_7D_2F_76',
				'Road_Detailmap_Opaque_Singlesided': '7B_7B_A2_8E',
				'Illuminance_Diffuse_1Bit_Doublesided': '7C_C6_D3_1D',
				'MetalSheen_Opaque_Doublesided': '7F_B8_3B_1A',
				'Vehicle_Opaque_PaintGloss_Textured_NormalMapped': '82_DE_22_8E',
				'FlashingNeon_Diffuse_1Bit_Doublesided': '86_6F_8D_FC',
				'Building_Night_Opaque_Singlesided': '89_41_8E_7B',
				'Foliage_1Bit_Doublesided': '8A_88_2A_56',
				'Vehicle_Opaque_PaintGloss_Textured': '8A_A0_FC_56',
				'Vehicle_Opaque_PlasticMatt': '8B_4D_5D_01',
				'Cable_GreyScale_Doublesided': '93_5F_33_58',
				'Diffuse_Opaque_Doublesided': '94_B4_DB_B5',
				'Tunnel_Lightmapped_Opaque_Singlesided2': '95_66_1E_23',
				'Vehicle_GreyScale_WheelChrome_Textured_Illuminance': '98_98_75_56',
				'Road_Night_Detailmap_Opaque_Singlesided': '9E_FB_32_8E',
				'Diffuse_1Bit_Singlesided': '9F_D5_D8_48',
				'Vehicle_1Bit_MetalFaded_Textured_EnvMapped': 'A2_14_84_00',
				'Specular_DetailMap_Opaque_Singlesided': 'A2_62_24_FC',
				'Tunnel_Lightmapped_Reflective_Opaque_Singlesided2': 'A6_28_0B_CF',
				'Tint_Specular_Opaque_Singlesided': 'AD_08_F1_AA',
				'Vehicle_Opaque_Chrome_Damaged': 'AD_23_5C_6B',
				'Specular_1Bit_Doublesided': 'AD_57_BF_E3',
				'Specular_Opaque_Doublesided': 'AE_B3_92_62',
				'Illuminance_Diffuse_Opaque_Singlesided': 'B0_1D_35_C6',
				'Terrain_Specular_Opaque_Singlesided': 'B1_2C_80_67',
				'DriveableSurface_Night_Detailmap_Opaque_Singlesided': 'B4_56_99_82',
				'Vehicle_Opaque_Metal_Textured': 'B4_A6_ED_D7',
				'Sign_Lightmap_Diffuse_Opaque_Singlesided': 'B6_7A_FA_60',
				'Glass_Specular_Transparent_Doublesided': 'B8_A1_8A_50',
				'Specular_1Bit_Singlesided': 'B8_A5_9E_01',
				'Lightmap_Diffuse_Opaque_Singlesided': 'B9_E2_4F_D0',
				'Sign_Specular_Opaque_Singlesided': 'BA_1F_F8_AC',
				'DriveableSurface_DetailMap_Diffuse_Opaque_Singlesided': 'BA_2E_9B_81',
				'DriveableSurface_Detailmap_Opaque_Singlesided': 'BD_2E_A8_C4',
				'FlashingNeon_Diffuse_Opaque_Singlesided': 'C0_04_1A_37',
				'Vehicle_GreyScale_WheelChrome_Textured_Damaged': 'C4_E3_58_7A',
				'Vehicle_GreyScale_Light_Textured_EnvMapped': 'C4_E4_B3_99',
				'Sign_Diffuse_1Bit_Singlesided': 'C5_1D_C5_57',
				'Specular_Greyscale_Doublesided': 'C7_1B_BF_08',
				'Illuminance_Diffuse_1Bit_Singlesided': 'D0_75_4B_DF',
				'Vehicle_Opaque_SimpleMetal_Textured': 'D2_CE_2F_51',
				'Tunnel_Lightmapped_Opaque_Doublesided2': 'D2_FB_F8_AB',
				'Tunnel_Lightmapped_Road_Detailmap_Opaque_Singlesided2': 'D4_90_D6_B8',
				'Vehicle_Opaque_NormalMap_SpecMap_Skin': 'D9_7E_0C_84',
				'Vehicle_Opaque_PaintGloss_Textured_Traffic': 'DB_62_6A_AE',
				'Vehicle_Opaque_Decal_Textured_EnvMapped': 'E1_C4_7C_19',
				'Vehicle_GreyScale_Decal_Textured': 'EA_27_69_B4',
				'CarStudio_DoNotShipWithThisInTheGame': 'EB_BF_C4_9D',
				'Tunnel_Diffuse_Opaque_Doublesided': 'F7_30_97_BD',
				'Tunnel_Diffuse_Opaque_Singlesided': 'FF_3B_D3_06'}
	
	try:
		mShaderId = shaders[shader_description]
	except:
		mShaderId = ""
		try:
			from difflib import get_close_matches
			shader_description_ = shader_description
			close_shaders = get_close_matches(shader_description, shaders.keys())
			for i in range(0, len(close_shaders)):
				if resource_type == "InstanceList":
					if not close_shaders[i].startswith("Vehicle"):
						shader_description = close_shaders[i]
						mShaderId = shaders[shader_description]
						print("WARNING: getting similar shader type for shader %s: %s" % (shader_description_, shader_description))
						break
				else:
					if close_shaders[i].startswith("Vehicle"):
						shader_description = close_shaders[i]
						mShaderId = shaders[shader_description]
						print("WARNING: getting similar shader type for shader %s: %s" % (shader_description_, shader_description))
						break
		except:
			mShaderId = ""
	if shader_description == "Godray_Additive_Doublesided_Default":
		shader_description = "Diffuse_1Bit_Doublesided"
		mShaderId = shaders[shader_description]
	return (mShaderId, shader_description)


def get_mShaderID_mw(shader_description, resource_type):
	shaders = {	'WorldPBR_Horizontal_VertexLit_Normal_Reflective_AO_Singlesided': '00_87_0F_00',
				'World_UVScrolling_Specular_Illuminance_Singlesided': '02_87_0F_00',
				'Blit2d_ViewGBufferSpecular': '02_E0_05_00',
				'Blit2d_ToRGBM': '05_E0_05_00',
				'WorldPBR_Building_PersistentLitWindows_InstanceAO_Singlesided_Lightmap': '06_D1_0D_00',
				'VehicleNFS13_Body_Driver': '08_15_1F_00',
				'WorldPBR_Building_LitWindows_InstanceAO_Singlesided_Lightmap': '0A_D1_0D_00',
				'World_GbufferBlend_Singlesided': '0B_85_0F_00',
				'TiledLighting_CopMulti4_WORLD1_CAR1': '0B_EC_09_00',
				'TiledLighting_CopMulti4_WORLD1_CAR0': '0D_EC_09_00',
				'VfxSplatter_Dynamic_Opaque': '0E_09_18_00',
				'WorldPBR_Diffuse_Normal_InstanceAO_Lightmap_Singlesided': '0E_D1_0D_00',
				'TiledLighting_CopMulti4_WORLD0_CAR1': '0F_EC_09_00',
				'TiledLighting_CopMulti3_WORLD1_CAR1': '11_EC_09_00',
				'VfxParticles_UVDistortion': '12_7E_0F_00',
				'Chevron': '13_78_00_00',
				'TiledLighting_CopMulti3_WORLD1_CAR0': '13_EC_09_00',
				'Deflicker_World_Diffuse_Specular_Overlay_Illuminance_Singlesided': '15_78_00_00',
				'TiledLighting_CopMulti3_WORLD0_CAR1': '15_EC_09_00',
				'Deflicker_World_Diffuse_Specular_Singlesided': '17_78_00_00',
				'TiledLighting_CopMulti2_WORLD1_CAR1': '17_EC_09_00',
				'VehicleNFS13_Body_Textured_NoDamage_NoEffects': '18_99_10_00',
				'TiledLighting_CopMulti2_WORLD1_CAR0': '19_EC_09_00',
				'WorldShadow_Opaque_Singlesided': '1A_0E_08_00',
				'WorldPBR_Diffuse_Normal_Specular_Reflective_AO_Lightmap_Singlesided': '1B_14_07_00',
				'TiledLighting_CopMulti2_WORLD0_CAR1': '1B_EC_09_00',
				'WorldShadow_Opaque_Doublesided': '1C_0E_08_00',
				'WorldPBR_Diffuse_Normal_Specular_Reflective_AO_1Bit_Lightmap_Singlesided': '1D_14_07_00',
				'World_Diffuse_Specular_Illuminance_Singlesided_InstanceAdditive': '1D_85_0F_00',
				'TiledLighting_CopMulti1_WORLD1_CAR1': '1D_EC_09_00',
				'PlotPBR_AO_Normal_Specular_Opaque_Lightmap_Singlesided': '1F_14_07_00',
				'TiledLighting_CopMulti1_WORLD1_CAR0': '1F_EC_09_00',
				'TiledLighting_CopMulti1_WORLD0_CAR1': '21_EC_09_00',
				'PlotPBR_DriveableGrass_AO_Normal_Specular_Opaque_Lightmap_Singlesided': '22_14_07_00',
				'WorldPBR_Diffuse_AO_Lightmap_1Bit_Doublesided': '22_3C_19_00',
				'Blit2d': '22_79_00_00',
				'Blit2d_AlphaAsColour': '23_79_00_00',
				'World_Diffuse_Specular_Singlesided_InstanceAdditive': '23_85_0F_00',
				'WorldPBR_Diffuse_Normal_Specular_Reflective_AO_Singlesided': '23_A7_06_00',
				'UIParticleShader': '24_2F_16_00',
				'Blit2d_AutomaticExposureMeter': '24_79_00_00',
				'WorldPBR_Diffuse_AO_1Bit_Doublesided': '25_3C_19_00',
				'Blit2d_ClearGBuffer': '25_79_00_00',
				'WorldPBR_Diffuse_Normal_Specular_Reflective_AO_ObjectTint_Lightmap_Singlesided': '26_7F_15_00',
				'Vfx_ShadowMapTest': '26_BE_07_00',
				'WorldPBR_Diffuse_AO_1Bit_Singlesided': '27_3C_19_00',
				'Blit2d_GammaCorrection': '27_79_00_00',
				'UINoiseShader': '27_CC_06_00',
				'TerrainPBR_Normal_Opaque_Singlesided': '27_F1_06_00',
				'BlobbyShadow_Greyscale_Doublesided': '29_79_00_00',
				'DriveableSurface_Lightmap': '2A_78_00_00',
				'Cable_GreyScale_Doublesided': '2A_79_00_00',
				'LightBuffer_KeylightAndAmbient_LightingOverrideHdrSphere': '2A_DE_04_00',
				'CatsEyes': '2B_79_00_00',
				'PlotPBR_AO_StandingWater_Opaque_Lightmap_Singlesided': '2B_86_0F_00',
				'CatsEyesGeometry': '2C_79_00_00',
				'Character_Greyscale_Textured_Doublesided_Skin': '2E_79_00_00',
				'DriveableSurface_DEPRECATED_RetroreflectivePaint_Lightmap': '2F_78_00_00',
				'Character_Opaque_Textured_NormalMap_SpecMap_Skin': '2F_79_00_00',
				'WorldPBR_Diffuse_Normal_ColouredSpecular_Reflective_AO_Doublesided': '2F_86_0F_00',
				'VfxParticles_DiffusePremultiplied_NoAlphaTest': '30_09_18_00',
				'PlotPBR_AO_Normal_Specular_Opaque_Singlesided': '30_13_07_00',
				'VfxParticles_CubeMap_GradientRemap': '31_2A_06_00',
				'ChevronBlockRoad': '31_79_00_00',
				'WorldPBR_Diffuse_Normal_ColouredSpecular_Reflective_AO_1Bit_Doublesided': '31_86_0F_00',
				'Fence_GreyScale_Doublesided': '32_78_00_00',
				'WorldPBR_Horizontal_PlanarReflection_VertexLit_Singlesided': '32_87_0F_00',
				'DebugIrradiance_1Bit_Singlesided_2d': '33_79_00_00',
				'Flag_UVFlip_Opaque_Doublesided': '33_86_0F_00',
				'Deflicker_WorldPBR_Emissive_Diffuse_Normal_Specular_Reflective_AO_Singlesided': '34_13_07_00',
				'Flag_Opaque_Doublesided': '34_78_00_00',
				'Diffuse_1Bit_Doublesided': '34_79_00_00',
				'WorldPBR_Horizontal_PlanarReflection_VertexLit_Lightmap_Singlesided': '34_87_0F_00',
				'KeyLightInScattering': '34_EC_09_00',
				'Water_Opaque_Singlesided': '35_0E_08_00',
				'DriveableSurface_FloatingDecal': '35_A7_06_00',
				'Diffuse_1Bit_Doublesided_Skin': '36_79_00_00',
				'WorldPBR_Diffuse_Normal_Specular_Reflective_AO_Doublesided': '37_0E_08_00',
				'DriveableSurface_FloatingDecal_1Bit': '37_A7_06_00',
				'FogAndBlurredKeyLightInScattering': '37_EC_09_00',
				'Diffuse_1Bit_Singlesided': '38_79_00_00',
				'Glass_Greyscale_Doublesided': '39_0B_08_00',
				'WorldPBR_FloatingDecal_RetroReflectivePaint_Normal_Specular_Reflective_AO_1Bit_Singlesided': '39_A7_06_00',
				'HelicopterRotor_GreyScale_Doublesided': '3B_78_00_00',
				'WorldPBR_FloatingDecal_Diffuse_Normal_Specular_Reflective_AO_Singlesided': '3B_A7_06_00',
				'Diffuse_Opaque_Singlesided': '3C_79_00_00',
				'BlurKeyLightInScattering': '3C_EC_09_00',
				'WorldPBR_FloatingDecal_Diffuse_Normal_Specular_Reflective_AO_1Bit_Singlesided': '3D_A7_06_00',
				'Diffuse_Opaque_Singlesided_Skin': '3E_79_00_00',
				'World_Diffuse_Specular_PersistentIlluminance_Singlesided': '3F_EB_0F_00',
				'BlurKeyLightInScattering2': '3F_EC_09_00',
				'Sign_RetroReflective': '40_78_00_00',
				'WorldPBR_Diffuse_Normal_Specular_Reflective_AO_PersistentLightmap_Singlesided': '41_86_0F_00',
				'WorldPBR_Diffuse_Normal_Specular_Reflective_AO_1Bit_PersistentLightmap_Singlesided': '41_EB_0F_00',
				'Blit2d_DepthOnly': '42_2A_13_00',
				'Tree_Translucent_1Bit_Doublesided_InstanceTint': '43_78_00_00',
				'DriveableSurface': '43_79_00_00',
				'DriveableSurface_AlphaMask': '44_79_00_00',
				'WorldPBR_Diffuse_Normal_Specular_Reflective_AO_Lightmap_Doublesided': '46_45_1C_00',
				'Water_Proto_Cheap': '46_78_00_00',
				'DriveableSurface_Decal': '46_79_00_00',
				'DriveableSurface_OBSOLETE_RetroreflectivePaint': '47_79_00_00',
				'DriveableSurface_DEPRECATED_Line_Lightmap_DirectionV': '48_79_00_00',
				'Skin_WorldPBR_Diffuse_Normal_Specular_Reflective_AO_Doublesided': '48_86_0F_00',
				'PlotPBR_Grass_AO_Normal_Opaque_Lightmap_Singlesided': '48_87_0F_00',
				'WorldPBR_Diffuse_Specular_AO_Lightmap_Doublesided': '49_45_1C_00',
				'DriveableSurface_DEPRECATED_Line_DirectionV': '4B_79_00_00',
				'World_Diffuse_Specular_1Bit_Lightmap_Doublesided': '4D_78_00_00',
				'World_Diffuse_Specular_FlashingNeon_Singlesided': '4F_78_00_00',
				'TerrainPBR_Normal_Opaque_Singlesided_Rough': '4F_87_0F_00',
				'World_Diffuse_Specular_Illuminance_Singlesided': '50_78_00_00',
				'FlaptGenericShader': '51_79_00_00',
				'ToneMapSetConstants': '51_9F_06_00',
				'FlaptGenericShader3D': '52_79_00_00',
				'PlotPBR_DriveableGrass_AO_Normal_Specular_Opaque_Lightmap_Singlesided_Rough': '53_87_0F_00',
				'Groundcover': '56_79_00_00',
				'PlotPBR_DriveableGrass_AO_Normal_Specular_Opaque_Singlesided_Rough': '56_87_0F_00',
				'PlotPBR_Grass_AO_Normal_Opaque_Lightmap_Singlesided_Rough': '58_87_0F_00',
				'Fog': '59_6E_07_00',
				'World_Diffuse_Specular_Singlesided': '59_78_00_00',
				'UISubtractiveShader': '5C_75_0F_00',
				'MapIconShader': '5D_79_00_00',
				'WorldPBR_Diffuse_Normal_Specular_Reflective_AO_1Bit_Lightmap_Doublesided': '5D_87_0F_00',
				'MapIconShaderSubtractive': '5E_75_0F_00',
				'NewSky': '5E_79_00_00',
				'UIDepthTestedShader': '5F_74_0C_00',
				'PlanarReflection_DepthBufferConversion_2d': '60_79_00_00',
				'Skin_World_Diffuse_Specular_1Bit_Singlesided': '61_7D_15_00',
				'WorldPBR_Building_PersistentLitWindows_InstanceAO_InstanceTint_Singlesided_Lightmap': '62_87_0F_00',
				'SeparableGaussian_2d': '63_79_00_00',
				'WorldPBR_NormalSpecInMap3_Normal_Specular_Illuminance_AO_Singlesided': '64_AE_19_00',
				'WorldPBR_Diffuse_Normal_ColouredSpecular_Reflective_AO_1Bit_Singlesided': '64_CC_12_00',
				'GBufferComposite': '66_78_00_00',
				'TerrainPBR_TangentSpaceNormal_Opaque_Singlesided_Rough': '66_AE_19_00',
				'VehicleNFS13_BodyPaint_TwoPaintMask_Lightmap': '66_EF_09_00',
				'TextAdditiveShader': '68_79_00_00',
				'VehicleNFS13_BodyPaint_TwoPaintMask': '68_EF_09_00',
				'GBufferCompositeNoMotionBlur': '69_78_00_00',
				'TextBoldDropShadow': '69_79_00_00',
				'GBufferCompositeRearViewMirror': '6A_78_00_00',
				'TextBoldShader': '6A_79_00_00',
				'VehicleNFS13_BodyPaint_TwoPaint_Lightmap': '6A_EF_09_00',
				'UIAdditiveDepthTestedShader': '6B_74_0C_00',
				'TextDropShadow': '6B_79_00_00',
				'LightBuffer_Cone': '6C_78_00_00',
				'TextGlow': '6C_79_00_00',
				'VehicleNFS13_BodyPaint_TwoPaint': '6C_EF_09_00',
				'LightBuffer_Cone2': '6D_78_00_00',
				'TextOutline': '6D_79_00_00',
				'LightBuffer_Cone3': '6E_78_00_00',
				'TextShader': '6E_79_00_00',
				'WorldPBR_Diffuse_Normal_ColouredSpecular_Reflective_AO_1Bit_Doublesided_Lightmap': '6E_8C_14_00',
				'VehicleNFS13_BodyPaint_NormalMap_NoDamage': '6E_EF_09_00',
				'UIRoadRibbonShader': '6F_2F_16_00',
				'LightBuffer_Cone4': '6F_78_00_00',
				'TriggerShader': '70_79_00_00',
				'VehicleNFS13_BodyPaint_Livery_Lightmap': '70_EF_09_00',
				'LightBuffer_Cop': '71_78_00_00',
				'UIAdditiveOverlayShader': '71_79_00_00',
				'WorldPBR_Diffuse_Normal_ColouredSpecular_Reflective_AO_Doublesided_Lightmap': '71_8C_14_00',
				'LightBuffer_Cop2': '72_78_00_00',
				'UIAdditivePixelate': '72_79_00_00',
				'VehicleNFS13_BodyPaint_Livery': '72_EF_09_00',
				'LightBuffer_Cop3': '73_78_00_00',
				'UIAdditiveShader': '73_79_00_00',
				'LightBuffer_Cop4': '74_78_00_00',
				'UIAutologShader': '74_79_00_00',
				'WorldPBR_Building_LitWindows_InstanceAO_InstanceTint_Singlesided_Lightmap': '74_87_0F_00',
				'VehicleNFS13_BodyPaint_Lightmap': '74_EF_09_00',
				'UIFlameShader': '75_79_00_00',
				'LightBuffer_KeylightAndAmbient': '76_78_00_00',
				'VfxParticles_Diffuse_GradientRemap': '76_90_04_00',
				'VehicleNFS13_BodyPaint': '76_EF_09_00',
				'UIGenericAlphaLuminanceShader': '77_79_00_00',
				'PlotPBR_TilingDecal_Opaque_Lightmap_Singlesided_Rough': '77_AE_19_00',
				'LightBuffer_KeylightAndAmbient_NoSpecular': '78_78_00_00',
				'UIGenericDestAlphaModulateShader': '78_79_00_00',
				'VehicleNFS13_Body_Textured_NormalMap_NoDamage': '78_EF_09_00',
				'LightBuffer_KeylightAndAmbient_ProjectedShadowTexture': '79_78_00_00',
				'UIMapShader': '79_79_00_00',
				'WorldPBR_Building_LitWindows_SliderBlend_Reflective_AO_Singlesided_Lightmap': '7A_14_07_00',
				'LightBuffer_KeylightAndAmbient_ProjectedShadowTexture_LowQuality': '7A_78_00_00',
				'UIMovieAdditiveShader': '7A_79_00_00',
				'PlotPBR_TilingDecal_DriveableGrass_Opaque_Lightmap_Singlesided_Rough': '7A_AE_19_00',
				'VehicleNFS13_Body_Textured_NormalMap_LocalEmissive': '7A_EF_09_00',
				'LightBuffer_KeylightAndAmbient_SingleCSM': '7B_78_00_00',
				'UIMovieShader': '7B_79_00_00',
				'LightBuffer_KeylightAndAmbient_SingleCSM_NoSpecular': '7C_78_00_00',
				'UIMovieShaderAddOverlay': '7C_79_00_00',
				'VehicleNFS13_Body_Textured_NormalMap_EmissiveFourChannel_NoDamage_NoEffects': '7C_EF_09_00',
				'WorldPBR_Diffuse_LOD2LitWindows_Singlesided_Lightmap': '7D_14_07_00',
				'LightBuffer_KeylightAndAmbient_NoShadow': '7D_78_00_00',
				'UIMovieShaderSubOverlay': '7D_79_00_00',
				'WorldPBR_Normal_TextureBlend_Reflective_AO_Lightmap_Singlesided': '7D_AE_19_00',
				'LightBuffer_Point': '7E_78_00_00',
				'UIRearViewMirrorShader': '7E_79_00_00',
				'PlotPBR_AO_Normal_Specular_Opaque_Singlesided_Rough': '7E_7C_15_00',
				'WorldPBR_Building_LitWindows_SliderBlend_Reflective_AO_InstanceIntensity_Singlesided_Lightmap': '7E_AE_19_00',
				'VehicleNFS13_Body_Textured_NormalMap_Lightmap': '7E_EF_09_00',
				'LightBuffer_Point2': '7F_78_00_00',
				'World_SmashedBillboard_InstanceDiffuse_Specular_Singlesided': '80_17_14_00',
				'LightBuffer_Point3': '80_78_00_00',
				'PlotPBR_AO_Normal_Specular_Opaque_Lightmap_Singlesided_Rough': '80_7C_15_00',
				'VehicleNFS13_Body_Textured_NormalMap': '80_EF_09_00',
				'LightBuffer_Point4': '81_78_00_00',
				'WorldPBR_Diffuse_Normal_Specular_Reflective_AO_InstanceIntensity_Lightmap_Singlesided': '82_AE_19_00',
				'VehicleNFS13_Body_Textured_Emissive_NoDamage_NoEffects': '82_EF_09_00',
				'LightBuffer_ProjectedTexture': '83_78_00_00',
				'VfxCorona_DiffusePremultiplied': '84_CC_12_00',
				'VehicleNFS13_Body_Textured_Lightmap': '84_EF_09_00',
				'WorldPBR_Diffuse_LOD2LitWindows_InstanceIntensity_Singlesided_Lightmap': '86_AE_19_00',
				'BilateralBlurSSAO': '86_CC_12_00',
				'VehicleNFS13_Body_Textured': '86_EF_09_00',
				'LightBuffer_VisionModeThermal': '87_BC_07_00',
				'UIDepthTestedScrollingShader': '88_7A_0F_00',
				'VehicleNFS13_Body_Lightmap': '88_EF_09_00',
				'WorldPBR_Diffuse_PersistentLOD2LitWindows_Singlesided': '89_86_0F_00',
				'WorldPBR_Building_PersistentLitWindows_InstanceIntensity_Reflective_AO_Singlesided_Lightmap': '8A_AE_19_00',
				'VehicleNFS13_Body_Alpha1bit_NormalMap_Textured_NoDamage': '8A_EF_09_00',
				'WorldPBR_Building_PersistentLitWindows_Reflective_AO_Singlesided_Lightmap': '8B_86_0F_00',
				'Blit2d_CompressToRGBG': '8B_EB_09_00',
				'VehicleNFS13_Body_Alpha1bit_NormalMap': '8C_EF_09_00',
				'WorldPBR_Building_PersistentLitWindows_Reflective_AO_Singlesided': '8E_86_0F_00',
				'UIPersistentImage_Additive': '8E_EB_09_00',
				'VehicleNFS13_Body_Alpha_NormalMap_Textured_NoDamage': '8E_EF_09_00',
				'WorldPBR_Diffuse_PersistentLOD2LitWindows_Singlesided_Lightmap': '90_86_0F_00',
				'VehicleNFS13_Body_Alpha_NormalMap_DoubleSided': '90_EF_09_00',
				'WorldPBR_Diffuse_Normal_Specular_InstanceTint_Singlesided': '91_7D_15_00',
				'GBufferCompositeVisionModeThermal': '91_BC_07_00',
				'WorldPBR_Building_PersistentLitWindows_InstanceAO_InstanceIntensity_Singlesided_Lightmap': '92_AE_19_00',
				'Blit2d_MaterialId': '92_EB_09_00',
				'VehicleNFS13_Body': '92_EF_09_00',
				'Skin_World_Diffuse_Specular_1Bit_Lightmap_Doublesided': '92_FA_0E_00',
				'WorldPBR_Diffuse_PersistentLOD2LitWindows_InstanceAO_Singlesided': '95_D2_0D_00',
				'Vfx_TyreMarksNew': '96_92_04_00',
				'WorldPBR_Diffuse_Normal_Specular_Reflective_AO_1Bit_Doublesided_Lightmap': '96_AE_19_00',
				'WorldPBR_Diffuse_LOD2LitWindows_InstanceAO_Singlesided': '98_D2_0D_00',
				'DownsampleMaterialDepthBoundStep1': '98_EB_09_00',
				'Blit2d_LinearToGammaWithMipChoice': '99_D4_10_00',
				'UIRibbonShader': '9A_7C_0F_00',
				'VfxParticles_Wireframe_Pretransformed': '9B_08_18_00',
				'WorldPBR_Diffuse_LOD2LitWindows_InstanceAO_Singlesided_Lightmap': '9B_D2_0D_00',
				'DownsampleMaterialDepthBound': '9B_EB_09_00',
				'VehicleNFS13_Body_Textured_NormalMap_Emissive_NoDamage_NoEffects': '9B_EF_09_00',
				'VehicleNFS13_Body_Textured_NormalMap_Lightmap_Licenseplate': '9C_D4_10_00',
				'VfxParticles_Wireframe': '9D_08_18_00',
				'Skin_WorldPBR_Diffuse_Normal_Specular_Reflective_AO_Singlesided': '9E_09_09_00',
				'TextureMemoryExport': '9E_EB_09_00',
				'VehicleNFS13_Refraction': 'A1_EF_09_00',
				'WorldPBR_Diffuse_Normal_ColouredSpecular_Reflective_AO_Singlesided': 'A2_0D_08_00',
				'TiledLightingPointLightsVisibility': 'A2_EB_09_00',
				'VehicleNFS13_Glass_Textured': 'A3_EF_09_00',
				'VfxSplatter_Overlay': 'A5_08_18_00',
				'VehicleNFS13_Glass_Doublesided': 'A5_EF_09_00',
				'PostFX_FisheyeHeatHaze': 'A6_D4_10_00',
				'WorldPBR_Building_LitWindows_ColouredSpecular_Reflective_AO_Singlesided': 'A7_0D_08_00',
				'VehicleNFS13_Glass_Textured_Lightmap': 'A7_EF_09_00',
				'TiledLightingSpotLightsVisibility': 'A8_EB_09_00',
				'WorldPBR_Diffuse_Normal_Specular_Reflective_AO_Singlesided_InstanceAdditive': 'A9_55_1D_00',
				'VehicleNFS13_Glass': 'A9_EF_09_00',
				'World_UVScrolling_Normal_Specular_1Bit_Singlesided': 'AA_45_1C_00',
				'CharacterNew_Opaque_Textured_Normal_Spec_VertexAO': 'AA_D4_10_00',
				'TiledLightingPointLights': 'AB_EB_09_00',
				'VehicleNFS13_Glass_Colourise': 'AB_EF_09_00',
				'WorldPBR_Diffuse_Normal_ColouredSpecular_Reflective_AO_PersistentLightmap_Singlesided': 'AC_7D_15_00',
				'DebugKeylightPlusIrradiance_1Bit_Singlesided_2d': 'AD_D4_10_00',
				'World_Diffuse_Specular_FlashingNeon_1_Bit_Singlesided': 'AE_13_07_00',
				'Blit2d_SwizzledDepthStencilToRGBA': 'AE_EB_09_00',
				'Vfx_Corona': 'AF_79_00_00',
				'DebugKeylight_1Bit_Singlesided_2d': 'AF_D4_10_00',
				'Vfx_CoronaFlare': 'B0_79_00_00',
				'Vfx_CoronaVisibilityTest': 'B1_79_00_00',
				'DebugCubemap_1Bit_Singlesided_2d': 'B1_D4_10_00',
				'TiledLighting_KeylightAndAmbientMain_WORLD1_CAR1': 'B1_EB_09_00',
				'PlotPBR_RGBDecal_Normal_Specular_Opaque_Lightmap_Singlesided_Rough': 'B2_55_1D_00',
				'VfxMesh': 'B3_79_00_00',
				'TiledLighting_KeylightAndAmbientMain_WORLD1_CAR0': 'B3_EB_09_00',
				'VehicleNFS13_Wheel_Textured_Normalmap_Blurred': 'B3_EF_09_00',
				'VfxMeshCarPaint': 'B4_79_00_00',
				'TextDropShadowDepthTested': 'B4_7A_0F_00',
				'VfxMeshNormalMap': 'B5_79_00_00',
				'TiledLighting_KeylightAndAmbientMain_WORLD0_CAR1': 'B5_EB_09_00',
				'VehicleNFS13_Wheel_Textured_Roughness': 'B5_EF_09_00',
				'VfxParticles_Diffuse_SubUV': 'B6_79_00_00',
				'VfxParticles_Diffuse': 'B7_79_00_00',
				'DriveableSurface_Lightmap_PlanarReflection': 'B8_33_23_00',
				'VfxParticles_Diffuse_AlphaErosion': 'B8_79_00_00',
				'VehicleNFS13_Wheel_Alpha_Textured_Normalmap_Blurred_Doublesided_PixelAO': 'B9_EF_09_00',
				'VfxParticles_DiffusePremultiplied': 'BA_79_00_00',
				'Glass_Interior_Greyscale_Singlesided': 'BB_33_23_00',
				'VehicleNFS13_Wheel_Tyre_Textured_Normalmap_Blurred': 'BB_5F_0F_00',
				'VfxParticles_DiffusePremultiplied_SubUV': 'BB_79_00_00',
				'Tree_Translucent_1Bit_Doublesided': 'BB_D4_10_00',
				'VehicleNFS13_Wheel_Alpha_Textured_Normalmap_BlurFade': 'BB_EF_09_00',
				'VfxParticles_MotionBlurSpriteUntex': 'BC_79_00_00',
				'Glass_Exterior_Greyscale_Singlesided': 'BD_33_23_00',
				'VehicleNFS13_Wheel_Alpha_Textured_Normalmap': 'BD_EF_09_00',
				'TiledLighting_PointMulti_WORLD0_CAR1': 'BE_EB_09_00',
				'WorldPBR_Diffuse_Normal_Specular_Reflective_InstanceAO_Lightmap_Singlesided': 'BF_E1_13_00',
				'VehicleNFS13_Wheel_Alpha1bit_Normalmap': 'BF_EF_09_00',
				'TiledLighting_PointMulti_WORLD1_CAR1': 'C0_EB_09_00',
				'TiledLighting_PointMulti_WORLD1_CAR0': 'C2_EB_09_00',
				'VfxSplatter_Dynamic': 'C4_08_18_00',
				'DriveableSurface_Decal_Lightmap': 'C5_C9_12_00',
				'VehicleNFS13_BodyPaint_TwoPaint_Livery_Lightmap': 'C6_EF_09_00',
				'UIStretched': 'C7_77_0F_00',
				'WorldPBR_Normal_TextureBlend_Reflective_AO_Singlesided': 'C8_81_06_00',
				'VehicleNFS13_BodyPaint_TwoPaint_Livery': 'C8_EF_09_00',
				'LinearizeDepth': 'C9_41_08_00',
				'TiledLighting_SpotMulti_WORLD1_CAR1': 'C9_EB_09_00',
				'WorldPBR_Building_LitWindows_SliderBlend_Reflective_AO_Singlesided': 'CB_13_07_00',
				'ComputeHBAO': 'CB_41_08_00',
				'TiledLighting_SpotMulti_WORLD1_CAR0': 'CB_EB_09_00',
				'Skin_World_Diffuse_Specular_Singlesided': 'CC_0A_08_00',
				'TiledLighting_SpotMulti_WORLD0_CAR1': 'CD_EB_09_00',
				'Blit2d_AllChannels': 'CF_41_08_00',
				'TiledLighting_CopMulti_WORLD1_CAR1': 'CF_EB_09_00',
				'TiledLighting_CopMulti_WORLD1_CAR0': 'D1_EB_09_00',
				'TextShaderDepthTested': 'D2_7A_0F_00',
				'TiledLighting_CopMulti_WORLD0_CAR1': 'D3_EB_09_00',
				'World_Weapon_Diffuse_Specular_Singlesided': 'D5_16_14_00',
				'Vfx_Weapon_TeflonSlick': 'D6_BD_07_00',
				'Skin_Weapon_World_Diffuse_Specular_Singlesided': 'D7_16_14_00',
				'LightBuffer_Spot4': 'DA_41_08_00',
				'WorldPBR_Diffuse_LOD2LitWindows_Singlesided': 'DB_11_07_00',
				'TiledLightingCopLightsVisibility': 'DB_EB_09_00',
				'LightBuffer_Spot3': 'DC_41_08_00',
				'PlotPBR_DriveableGrass_AO_Normal_Specular_Opaque_Singlesided': 'DE_0A_08_00',
				'LightBuffer_Spot2': 'DE_41_08_00',
				'TiledLighting_KeylightAndAmbientMain_WORLD0_CAR1_SHADOW0': 'DE_EB_09_00',
				'LightBuffer_Spot': 'E0_41_08_00',
				'TiledLighting_KeylightAndAmbientMain_WORLD1_CAR1_SHADOW0': 'E0_EB_09_00',
				'BlitGBufferVITA': 'E1_F2_09_00',
				'TiledLighting_KeylightAndAmbientMain_WORLD1_CAR0_SHADOW0': 'E2_EB_09_00',
				'UIPersistentImage': 'E3_7C_0F_00',
				'TiledLighting_PointMulti4_WORLD1_CAR1': 'E7_EB_09_00',
				'PostAA': 'E8_DF_05_00',
				'TiledLighting_PointMulti4_WORLD1_CAR0': 'E9_EB_09_00',
				'TiledLighting_PointMulti4_WORLD0_CAR1': 'EB_EB_09_00',
				'Blit2d_SimpleColourWrite': 'EC_DF_05_00',
				'TiledLighting_PointMulti3_WORLD1_CAR1': 'ED_EB_09_00',
				'DriveableSurface_FloatingDecal_Lightmap_1Bit': 'EF_56_09_00',
				'TiledLighting_PointMulti3_WORLD1_CAR0': 'EF_EB_09_00',
				'Blit2d_BiCubicH': 'F0_4E_16_00',
				'Blit2d_GeneratePCTonemapConstants_AverageLumaFinal': 'F0_DF_05_00',
				'CombineLdrParticleIntoHdrBuffer': 'F1_90_0B_00',
				'TiledLighting_PointMulti3_WORLD0_CAR1': 'F1_EB_09_00',
				'LightBuffer_Line': 'F2_41_08_00',
				'DriveableSurface_FloatingDecal_Lightmap': 'F2_56_09_00',
				'Blit2d_GeneratePCTonemapConstants_BuildConstant': 'F2_DF_05_00',
				'TiledLighting_PointMulti2_WORLD1_CAR1': 'F3_EB_09_00',
				'Blit2d_GeneratePCTonemapConstants_AverageLuma': 'F4_DF_05_00',
				'LightBuffer_Line3': 'F5_41_08_00',
				'WorldPBR_Diffuse_Normal_Specular_Reflective_AO_1Bit_Doublesided': 'F5_85_0F_00',
				'TiledLighting_PointMulti2_WORLD1_CAR0': 'F5_EB_09_00',
				'WorldPBR_Diffuse_Normal_Specular_Reflective_AO_1Bit_Singlesided': 'F6_F0_06_00',
				'LightBuffer_Line2': 'F7_41_08_00',
				'TiledLighting_PointMulti2_WORLD0_CAR1': 'F7_EB_09_00',
				'Deflicker_WorldPBR_Diffuse_Normal_Specular_Reflective_AO_Singlesided': 'F8_12_07_00',
				'LightBuffer_Line4': 'F9_41_08_00',
				'FastDepthRestore': 'F9_90_0B_00',
				'MapIconShaderAdditive': 'F9_AA_05_00',
				'WorldPBR_Diffuse_Normal_ColouredSpecular_Reflective_AO_Lightmap_Singlesided': 'F9_D0_0D_00',
				'LightBuffer_KeylightAndAmbient_EnvironmentMap': 'F9_DF_05_00',
				'TiledLighting_PointMulti1_WORLD1_CAR1': 'F9_EB_09_00',
				'Character_GPMM_Glass_Textured_Doublesided_Skin': 'F9_EE_09_00',
				'TiledLighting_PointMulti1_WORLD1_CAR0': 'FB_EB_09_00',
				'FastDepthRestoreFinalTileTouch': 'FC_90_0B_00',
				'VehicleNFS13_Wheel_Alpha1bit_Textured_Normalmap': 'FC_BF_19_00',
				'VfxParticles_Diffuse_SubUV_NoBlend': 'FD_0A_08_00',
				'TiledLighting_PointMulti1_WORLD0_CAR1': 'FD_EB_09_00',
				'Deflicker_WorldPBR_Diffuse_Normal_Specular_Reflective_AO_Doublesided': 'FE_CF_0D_00',
				'LightBuffer_KeylightAndAmbient_DebugLighting': 'FF_DF_05_00'}
	
	# Adding custom shaders
	try:
		shaders.update(custom_shaders_mw())
	except:
		print("WARNING: custom_shaders function not found. Custom data will not be available.")
		shaders['Glass'] = 'A9_EF_09_00' #before it was A7_EF_09_00
		shaders['Glass_Black'] = 'A9_EF_09_00'
		shaders['Glass_black'] = 'A9_EF_09_00'
		shaders['VehicleNFS13_Mirror'] = 'A9_EF_09_00'
		shaders['Mirror'] = 'A9_EF_09_00'
		shaders['VehicleNFS13_Body_Chrome'] = '92_EF_09_00'
		shaders['VehicleNFS13_Chrome'] = '92_EF_09_00'
		shaders['Chrome'] = '92_EF_09_00'
		shaders['VehicleNFS13_Body_Tyre'] = '9B_EF_09_00'
		shaders['VehicleNFS13_Tyre'] = '9B_EF_09_00'
		shaders['Tyre'] = '9B_EF_09_00'
		shaders['Tire'] = '9B_EF_09_00'
		shaders['Licenseplate'] = '7E_EF_09_00'
		shaders['LicensePlate'] = '7E_EF_09_00'
		shaders['License_Plate'] = '7E_EF_09_00'
		shaders['VehicleNFS13_Licenseplate'] = '7E_EF_09_00'
		shaders['VehicleNFS13_License_Plate'] = '7E_EF_09_00'
		shaders['LicensePlate_Number'] = '9C_D4_10_00'
		shaders['Licenseplate_Number'] = '9C_D4_10_00'
		shaders['License_Plate_Number'] = '9C_D4_10_00'
		shaders['VehicleNFS13_Licenseplate_Number'] = '9C_D4_10_00'
		shaders['VehicleNFS13_License_Plate_Number'] = '9C_D4_10_00'
		shaders['DullPlastic'] = '92_EF_09_00'
		shaders['Dull_Plastic'] = '92_EF_09_00'
		shaders['Interior'] = '9B_EF_09_00'
		shaders['VehicleNFS13_Interior'] = '9B_EF_09_00'
		shaders['Metal'] = '72_EF_09_00'
		shaders['BodyPaint_Livery'] = '72_EF_09_00'
		shaders['BodyLivery'] = '72_EF_09_00'
		shaders['BodyPaint'] = '76_EF_09_00'
		shaders['BodyColor'] = '92_EF_09_00'
		shaders['Badge'] = '8A_EF_09_00'
		shaders['Emblem'] = '8A_EF_09_00'
		shaders['Symbol'] = '8A_EF_09_00'
		shaders['Grill'] = '8A_EF_09_00'
		shaders['Transparent'] = '8A_EF_09_00'
		shaders['VehicleNFS13_Caliper'] = 'B5_EF_09_00'
		shaders['Caliper'] = 'B5_EF_09_00'
		shaders['Caliper_Textured'] = 'B5_EF_09_00'
		shaders['VehicleNFS13_BrakeDisc'] = 'B5_EF_09_00'
		shaders['BrakeDisc'] = 'B5_EF_09_00'
		shaders['VehicleNFS13_Chassis'] = '78_EF_09_00'
		shaders['Chassis'] = '78_EF_09_00'
		shaders['VehicleNFS13_Carbonfiber'] = '78_EF_09_00'
		shaders['CarbonFiber'] = '78_EF_09_00'
		shaders['LightCluster'] = '7C_EF_09_00'
		shaders['LightRefracted'] = 'A1_EF_09_00'
		shaders['Rim'] = 'B5_EF_09_00'
		shaders['RimFade'] = 'B9_EF_09_00'
		shaders['RimBlur'] = 'B9_EF_09_00'
		shaders['RimSpin'] = 'B9_EF_09_00'
		shaders['CarbonFiber2'] = '78_EF_09_00'
		shaders['GlassColourise'] = 'AB_EF_09_00'
		shaders['GlassColour'] = 'AB_EF_09_00'
		shaders['GlassColor'] = 'AB_EF_09_00'
		shaders['CopLight'] = '7A_EF_09_00'
		shaders['CarPaint'] = '76_EF_09_00'
		shaders['CaliperBadge'] = 'FC_BF_19_00'
		shaders['RimBadge'] = 'FC_BF_19_00'
		shaders['RimBadgeFade'] = 'BB_EF_09_00'
		shaders['BodypaintLight'] = '74_EF_09_00'
		shaders['CarpaintLight'] = '74_EF_09_00'
		shaders['BodyPaintNormal'] = '6E_EF_09_00'
		shaders['CarPaintNormal'] = '6E_EF_09_00'
		shaders['LightGlass'] = 'A7_EF_09_00'
		shaders['Engine'] = '78_EF_09_00'
		#CharacterSpec
		shaders['Character'] = 'AA_D4_10_00'
		shaders['Driver'] = 'AA_D4_10_00'
	
	try:
		mShaderId = shaders[shader_description]
	except:
		mShaderId = ""
		try:
			from difflib import get_close_matches
			shader_description_ = shader_description
			close_shaders = get_close_matches(shader_description, shaders.keys())
			for i in range(0, len(close_shaders)):
				if resource_type == "InstanceList":
					if not close_shaders[i].startswith("VehicleNFS13"):
						shader_description = close_shaders[i]
						mShaderId = shaders[shader_description]
						print("WARNING: getting similar shader type for shader %s: %s" % (shader_description_, shader_description))
						break
				elif resource_type == "CharacterSpec":
					if close_shaders[i].startswith("Character"):
						shader_description = close_shaders[i]
						mShaderId = shaders[shader_description]
						print("WARNING: getting similar shader type for shader %s: %s" % (shader_description_, shader_description))
						break
				else:
					if close_shaders[i].startswith("VehicleNFS13"):
						shader_description = close_shaders[i]
						mShaderId = shaders[shader_description]
						print("WARNING: getting similar shader type for shader %s: %s" % (shader_description_, shader_description))
						break
		except:
			mShaderId = ""
		if mShaderId == "":
			if resource_type == "InstanceList":
				shader_description = 'WorldPBR_Diffuse_Normal_Specular_Reflective_AO_1Bit_Singlesided'
				mShaderId = shaders[shader_description]
			elif resource_type == "GraphicsSpec":
				shader_description = 'VehicleNFS13_BodyPaint_Livery'
				mShaderId = shaders[shader_description]
			elif resource_type == "WheelGraphicsSpec":
				shader_description = 'VehicleNFS13_Wheel_Textured_Roughness'
				mShaderId = shaders[shader_description]
			elif resource_type == "CharacterSpec":
				shader_description = 'CharacterNew_Opaque_Textured_Normal_Spec_VertexAO'
				mShaderId = shaders[shader_description]
	
	mShaderId = shaders[shader_description]
	return (mShaderId, shader_description)


def get_mShaderID_hp(shader_description, resource_type):
	shaders = {	'UIMapShader': '00_2F_0C_00',
				'UIFlameShaderNonAdditive': '01_66_0B_00',
				'World_Diffuse_Dirt_Normal_Specular_Overlay_Singlesided': '02_E8_12_00',
				'Vehicle_1Bit_Textured_NormalMapped_Emissive_AO_Livery': '06_35_03_00',
				'VfxMesh': '06_93_03_00',
				'World_Diffuse_Specular_Normal_Parallax_Singlesided': '06_E8_12_00',
				'Deflicker_World_Diffuse_Normal_Specular_Singlesided': '08_E8_12_00',
				'Deflicker_World_Diffuse_Normal_Specular_Overlay_Singlesided': '0A_E8_12_00',
				'World_Diffuse_Reflective_Overlay_Lightmap_Singlesided': '0B_6C_07_00',
				'Deflicker_World_Diffuse_Normal_Specular_Overlay_IlluminanceNight_Singlesided': '0C_E8_12_00',
				'Deflicker_World_Diffuse_Normal_Specular_Overlay_Illuminance_Singlesided': '0E_E8_12_00',
				'World_Diffuse_Specular_Overlay_IlluminanceNight_1Bit_Singlesided': '10_1A_09_00',
				'Vehicle_Opaque_Two_PaintGloss_Textured_LightmappedLights_Livery_Wrap': '10_AF_13_00',
				'World_DiffuseBlend_Normal_Overlay_Lightmap_Singlesided': '12_1A_09_00',
				'Vehicle_Opaque_PaintGloss_Textured_LightmappedLights_ColourOverride_Wrap': '12_AF_13_00',
				'World_Diffuse_Specular_Singlesided': '13_2F_06_00',
				'World_Diffuse_1Bit_Dirt_Normal_Specular_Overlay_Singlesided': '13_E8_12_00',
				'World_Diffuse_Specular_1Bit_Lightmap_Doublesided': '14_1A_09_00',
				'Vehicle_Glass_Emissive_Coloured_Singlesided_Wrap': '14_AF_13_00',
				'Cable_GreyScale_Doublesided': '15_14_00_00',
				'Vehicle_Opaque_Emissive_AO': '19_D4_03_00',
				'SSAO': '19_E8_12_00',
				'Vehicle_Opaque_Emissive_Reflective_AO': '1B_D4_03_00',
				'World_Normal_Specular_Overlay_Singlesided': '1C_31_06_00',
				'TextBoldShader': '1C_8C_04_00',
				'World_Diffuse_Specular_Parallax_Singlesided': '1D_2F_06_00',
				'Blur': '1D_E8_12_00',
				'TriggerShader': '1E_67_03_00',
				'Flag_Opaque_Doublesided': '1F_1A_09_00',
				'World_Diffuse_Specular_Overlay_Singlesided': '1F_2F_06_00',
				'TextDropShadow': '1F_8C_04_00',
				'LightBuffer_Cone4': '20_95_09_00',
				'World_Diffuse_Dirt_Normal_SpecMap_Overlay_Singlesided': '20_E8_12_00',
				'LightBuffer_KeylightAndAmbient_ProjectedShadowTexture': '21_73_03_00',
				'VfxMeshNormalMap': '21_93_03_00',
				'TextShader': '22_8C_04_00',
				'LightBuffer_Point4': '22_95_09_00',
				'VfxMeshCarPaint': '23_93_03_00',
				'DEBUG_TRIGGER_Illuminance_Greyscale_Singlesided': '23_D0_02_00',
				'TextBoldDropShadow': '24_8C_04_00',
				'DriveableSurface_Car_Select': '24_E8_12_00',
				'CatsEyes': '25_92_03_00',
				'World_DiffuseBlend_Normal_Overlay_Singlesided': '27_6E_07_00',
				'TextOutline': '27_8C_04_00',
				'Vfx_CoronaBeam': '27_E8_12_00',
				'DiffuseSpecmapNormalMap_DirtMap': '28_6C_07_00',
				'LightBuffer_Cone3': '28_95_09_00',
				'Tree_Translucent_1Bit_Doublesided': '29_1A_09_00',
				'World_Diffuse_Normal_SpecMap_Singlesided': '29_E8_12_00',
				'LightBuffer_Cone2': '2A_95_09_00',
				'Vehicle_1Bit_Textured_NormalMapped_Reflective_Emissive_AO_Livery': '2B_58_05_00',
				'DriveableSurface_Car_Select_Simple': '2B_E8_12_00',
				'LightBuffer_Point3': '2D_95_09_00',
				'World_Diffuse_Normal_SpecMap_Overlay_Singlesided': '2D_E8_12_00',
				'Diffuse_Greyscale_Doublesided': '2E_1D_00_00',
				'LightBuffer_Point2': '2F_95_09_00',
				'Vehicle_Glass_Coloured_NoNormalMap': '2F_E8_12_00',
				'Vehicle_Glass_Emissive_Coloured_NoNormalMap': '31_E8_12_00',
				'World_DiffuseBlend_Normal_Overlay_LightmapNight_Singlesided': '33_1A_09_00',
				'Vehicle_Glass_Emissive_Coloured_Singlesided_NoNormalMap': '33_E8_12_00',
				'DICETerrain3_Proto': '35_0E_05_00',
				'World_Diffuse_Specular_1Bit_LightmapNight_Doublesided': '35_1A_09_00',
				'Vehicle_Glass_LocalEmissive_Coloured_NoNormalMap': '35_E8_12_00',
				'Road_Proto': '36_30_02_00',
				'World_Diffuse_Specular_Overlay_LightmapNight_Singlesided': '36_6E_07_00',
				'LightBuffer_Cop4': '36_95_09_00',
				'World_Normal_Specular_Overlay_LightmapNight_Singlesided': '38_6E_07_00',
				'LightBuffer_Cop3': '38_95_09_00',
				'World_Diffuse_Specular_Normal_Parallax_WindowTex_Singlesided': '39_E8_12_00',
				'HidingSpot_Proto_LightmapNight': '3A_6E_07_00',
				'LightBuffer_Cop2': '3A_95_09_00',
				'Vehicle_Wheel_Alpha_Normalmap': '3B_58_05_00',
				'GBufferCompositeRearViewMirror': '3C_73_03_00',
				'LightBuffer_Cop': '3C_95_09_00',
				'World_Diffuse_Specular_Normal_Overlay_Lightmap_Singlesided': '3C_E8_12_00',
				'FlaptGenericShader3D': '3D_CD_03_00',
				'World_Diffuse_Reflective_Overlay_LightmapNight_Singlesided': '3E_6E_07_00',
				'DriveableSurface_AlphaMask_LightmapNight': '40_6E_07_00',
				'Diffuse_Opaque_Singlesided_Skin_ObjectAO': '40_73_03_00',
				'Vehicle_Opaque_PaintGloss_Textured_LightmappedLights_ColourOverride': '41_C6_01_00',
				'DriveableSurface_LightmapNight': '42_6E_07_00',
				'Diffuse_Opaque_Singlesided_ObjectAO': '42_73_03_00',
				'Vehicle_Wheel_1Bit_Alpha_Normalmap': '43_52_04_00',
				'BlitBilateralUpsample': '43_93_03_00',
				'Vehicle_Glass_Coloured': '43_C6_01_00',
				'DriveableSurface_Decal_LightmapNight': '44_6E_07_00',
				'Diffuse_Greyscale_Doublesided_ObjectAO': '44_73_03_00',
				'Vehicle_Wheel_1Bit_Alpha': '45_52_04_00',
				'GBufferComposite': '45_61_04_00',
				'Vehicle_Glass_Emissive_Coloured': '45_C6_01_00',
				'World_CopStudio_Specular_Reflective_Singlesided': '46_0F_05_00',
				'DriveableSurface_RetroreflectivePaint_LightmapNight': '46_6E_07_00',
				'Diffuse_1Bit_Singlesided_ObjectAO': '46_73_03_00',
				'VfxParticles_MotionBlurSpriteUntex': '46_92_03_00',
				'Diffuse_1Bit_Doublesided_Skin_ObjectAO': '48_73_03_00',
				'HelicopterRotor_GreyScale_Doublesided': '49_31_06_00',
				'Vehicle_Opaque_Textured_Phong': '4A_62_02_00',
				'Diffuse_1Bit_Doublesided_ObjectAO': '4A_73_03_00',
				'LineariseDepthDownsample': '4C_E8_12_00',
				'Vehicle_Opaque_Textured_Normalmapped_Reflective_AO': '4E_62_02_00',
				'Vehicle_Greyscale_Textured_Normalmapped_Reflective': '50_62_02_00',
				'Vehicle_Opaque_PaintGloss_Textured_LightmappedLights_Livery': '52_C6_01_00',
				'DICETerrain3Cheap_Proto': '53_6B_07_00',
				'Vehicle_Opaque_Textured_Reflective': '54_62_02_00',
				'World_Diffuse_Specular_Overlay_IlluminanceNight_Singlesided': '55_18_09_00',
				'LightBuffer_KeylightAndAmbient_ProjectedShadowTexture_LowQuality': '55_73_03_00',
				'Vehicle_Opaque_Textured': '56_62_02_00',
				'DriveableSurface_Lightmap_Car_Select': '56_C4_07_00',
				'Vehicle_Opaque_PaintGloss_Textured_LightmappedLights_ColourOverride_Livery': '56_C6_01_00',
				'Vehicle_Opaque_Textured_Normalmapped_AO': '58_62_02_00',
				'Blit2d': '59_03_04_00',
				'Diffuse_Opaque_Singlesided': '5A_17_00_00',
				'Flag_VerticalBanner_Opaque_Doublesided': '5A_1A_09_00',
				'DriveableSurface_RetroreflectivePaint_Lightmap_Car_Select': '5A_C4_07_00',
				'LightBuffer_Point': '5B_C6_01_00',
				'Foliage_1Bit_Doublesided': '5D_03_04_00',
				'Vehicle_Opaque_Two_PaintGloss_Textured_LightmappedLights_Livery': '5D_52_04_00',
				'LightBuffer_Cone': '5D_C6_01_00',
				'Diffuse_1Bit_Doublesided': '5E_17_00_00',
				'Water_Proto_Cheap': '5E_18_09_00',
				'NewSky': '60_93_08_00',
				'PlanarReflection_DepthBufferConversion_2d': '61_03_04_00',
				'Illuminance_Diffuse_Opaque_Singlesided': '61_17_00_00',
				'DiffuseSpecmapNormalMap': '61_C6_01_00',
				'UIMovieShader': '62_8C_03_00',
				'SeparableGaussian_2d': '63_03_04_00',
				'World_Tourbus_Normal_Reflective_Overlay_Singlesided': '63_2D_0C_00',
				'DriveableSurface_AlphaMask_Lightmap': '63_6B_07_00',
				'Armco_Opaque_Doublesided': '63_7F_02_00',
				'DriveableSurface_Lightmap': '65_6B_07_00',
				'LightBuffer_KeylightAndAmbientNoShadow': '66_03_04_00',
				'DriveableSurface_Decal_Lightmap': '67_6B_07_00',
				'UIGenericDestAlphaModulateShader': '68_93_08_00',
				'LightBuffer_KeylightAndAmbient': '68_C6_01_00',
				'DriveableSurface_RetroreflectivePaint_Lightmap': '69_6B_07_00',
				'UIGenericAlphaLuminanceShader': '6A_93_08_00',
				'HidingSpot_Proto_Lightmap': '6B_6B_07_00',
				'UIAutologShader': '6B_CD_03_00',
				'UIMovieAdditiveShader': '6E_8C_03_00',
				'Blit2d_GammaCorrection': '70_03_04_00',
				'VfxParticles_DiffusePremultiplied': '70_92_03_00',
				'Blit2d_AlphaAsColour': '73_03_04_00',
				'Chevron': '74_1A_09_00',
				'Bush_Translucent_1Bit_Doublesided': '74_2D_0C_00',
				'LightBuffer_KeylightAndAmbient_SingleCSM': '76_03_04_00',
				'VfxParticles_Diffuse_AlphaErosion': '78_FF_07_00',
				'Blit2d_ClearGBuffer': '79_03_04_00',
				'TextGlow': '79_8B_03_00',
				'UIRearViewMirrorShader': '79_8C_03_00',
				'Foliage_LargeSprites_Proto': '7B_18_09_00',
				'GBufferCompositeNoFog': '7C_03_04_00',
				'VfxParticles_Diffuse_AlphaErosion_SubUV': '7D_FF_07_00',
				'LightBuffer_KeylightAndAmbient_SingleCSM_NoSpecular': '7F_03_04_00',
				'LightBuffer_KeylightAndAmbient_NoSpecular': '81_03_04_00',
				'Vfx_SkidMarks': '82_92_01_00',
				'TextAdditiveShader': '83_8C_03_00',
				'Vehicle_Glass_Emissive_Coloured_Singlesided': '84_52_04_00',
				'Vehicle_Opaque_Textured_NormalMapped_Reflective_LocalEmissive_AO': '85_0A_0A_00',
				'GBufferCompositeDepthWrite': '86_03_04_00',
				'DiffuseSpecNormalMap_1Bit': '86_B5_03_00',
				'DriveableSurface_RetroreflectivePaint_LineFade': '8A_03_04_00',
				'Vehicle_Opaque_Textured_NormalMapped_Reflective_Emissive_AO': '8A_62_02_00',
				'CatsEyesGeometry': '8B_93_03_00',
				'DriveableSurface_RetroreflectivePaint_Lightmap_LineFade': '8C_03_04_00',
				'World_Diffuse_Specular_Reflective_Singlesided': '8C_6C_07_00',
				'Blit2d_EdgeDetect_MotionBlur': '8F_03_04_00',
				'Diffuse_1Bit_Doublesided_Skin': '95_26_04_00',
				'Diffuse_1Bit_Singlesided': '97_1A_00_00',
				'Diffuse_Opaque_Singlesided_Skin': '97_26_04_00',
				'DriveableSurface': '97_92_03_00',
				'ChevronBlockRoad': '99_48_06_00',
				'Foliage_Proto': '9A_0D_05_00',
				'World_Normal_Specular_Overlay_Lightmap_Singlesided': '9B_6A_07_00',
				'World_Diffuse_Specular_Overlay_Lightmap_Singlesided': '9D_6A_07_00',
				'UIAdditiveOverlayShader': '9E_8C_03_00',
				'DriveableSurface_Decal': 'A3_92_03_00',
				'UIFlameShader': 'A3_CD_03_00',
				'HidingSpot_Proto': 'A4_30_06_00',
				'DriveableSurface_AlphaMask': 'A5_92_03_00',
				'DriveableSurface_RetroreflectivePaint': 'A7_92_03_00',
				'Water_Proto': 'AC_30_06_00',
				'Fence_GreyScale_Doublesided': 'AF_6C_07_00',
				'DriveableSurface_RetroreflectivePaint_LineFade_Rotated_UV': 'B0_2E_0C_00',
				'World_Normal_Reflective_Overlay_Lightmap_Singlesided': 'B0_4E_08_00',
				'UIAdditivePixelate': 'B5_8C_03_00',
				'Skin_World_Diffuse_Specular_Overlay_Singlesided': 'B7_6C_07_00',
				'Vehicle_Opaque_PaintGloss_Textured_LightmappedLights': 'B8_1E_00_00',
				'Vehicle_Opaque_PaintGloss_Textured_LightmappedLights_Livery_Wrap': 'B8_6C_13_00',
				'DriveableSurface_CarPark': 'BA_1B_09_00',
				'UIMovieShaderSubOverlay': 'BA_57_0B_00',
				'Vehicle_Opaque_PaintGloss_Textured_LightmappedLights_Wrap': 'BA_6C_13_00',
				'UIAdditiveShader': 'BA_8B_03_00',
				'Vehicle_Tyre': 'BB_1E_00_00',
				'DriveableSurface_AlphaMask_CarPark': 'BC_1B_09_00',
				'Vehicle_Wheel_Alpha_Blur_Normalmap': 'BC_1E_00_00',
				'UIMovieShaderAddOverlay': 'BC_57_0B_00',
				'Vehicle_Wheel_Opaque': 'BD_1E_00_00',
				'VfxParticles_Diffuse': 'BD_92_01_00',
				'DriveableSurface_RetroreflectivePaint_CarPark': 'BE_1B_09_00',
				'Vehicle_Wheel_Opaque_Blur': 'BE_1E_00_00',
				'DriveableSurface_Decal_CarPark': 'C0_1B_09_00',
				'DriveableSurface_RetroreflectivePaint_LineFade_Rotated_UV_02': 'C0_2E_0C_00',
				'Vfx_Corona': 'C2_92_01_00',
				'DiffuseSpecmapNormalMap_Overlay': 'C6_30_06_00',
				'Vfx_CoronaVisibilityTest': 'C9_92_01_00',
				'Character_Opaque_Textured_NormalMap_SpecMap_Skin': 'CB_51_04_00',
				'Vfx_CoronaFlare': 'CB_92_01_00',
				'Vehicle_Wheel_Brakedisc_1Bit_Blur_Normalmap': 'CB_A9_01_00',
				'Waterfall_Proto': 'CD_30_06_00',
				'Vehicle_Opaque_Textured_NormalMapped_Emissive_AO': 'CD_D0_03_00',
				'Character_Greyscale_Textured_Doublesided_Skin': 'CF_51_04_00',
				'VfxParticles_DiffusePremultiplied_SubUV': 'CF_6E_07_00',
				'Sign_RetroReflective': 'D2_B6_03_00',
				'DICETerrain3NoRGB_Proto': 'D9_1B_09_00',
				'Vehicle_Glass_Emissive_Coloured_Wrap': 'DB_6C_13_00',
				'Fence_GreyScale_Singlesided': 'DC_0E_05_00',
				'MapIconShader': 'DD_9A_05_00',
				'Groundcover_Proto': 'DE_72_03_00',
				'Skin_World_Diffuse_Specular_Reflective_Singlesided': 'DF_6C_07_00',
				'Foliage_1Bit_Normal_Spec_Doublesided': 'DF_E7_12_00',
				'VfxParticles_Diffure_SubUV': 'E0_FE_07_00',
				'Bush_Translucent_1Bit_Normal_Spec_Doublesided': 'E1_E7_12_00',
				'Deflicker_World_Diffuse_Specular_Singlesided': 'E2_0E_05_00',
				'DICETerrain3CliffsOnly_Proto': 'E2_1B_09_00',
				'BlobbyShadow_Greyscale_Doublesided': 'E3_13_00_00',
				'Deflicker_World_Diffuse_Specular_Overlay_Singlesided': 'E4_0E_05_00',
				'Foliage_Proto_Spec_Normal': 'E5_E7_12_00',
				'Deflicker_World_Diffuse_Specular_Overlay_Illuminance_Singlesided': 'E6_0E_05_00',
				'Vehicle_Glass_LocalEmissive_Coloured': 'E6_92_01_00',
				'Foliage_LargeSprites_Proto_Spec_Normal': 'E7_E7_12_00',
				'World_Diffuse_Specular_Overlay_Illuminance_Singlesided': 'E8_6A_07_00',
				'DebugIrradiance_1Bit_Singlesided_2d': 'EA_13_00_00',
				'World_Diffuse_Specular_Illuminance_Singlesided': 'EB_6A_07_00',
				'Vehicle_Rearlights_Heightmap': 'EB_6E_03_00',
				'World_DiffuseBlend_Specular_Overlay_Singlesided': 'F1_30_06_00',
				'Vehicle_1Bit_Textured_Normalmapped_Reflective': 'F1_D3_03_00',
				'Deflicker_World_Diffuse_Specular_Overlay_IlluminanceNight_Singlesided': 'F1_D8_0B_00',
				'Vehicle_Opaque_Textured_NormalMapped_Reflective_Emissive_AO_Livery': 'F3_D0_03_00',
				'Vehicle_Opaque_Reflective': 'F3_D3_03_00',
				'LightBuffer_ProjectedTexture': 'F6_6E_03_00',
				'DriveableSurface_RetroreflectivePaint_Lightmap_LineFade_rotatedUV': 'F9_2E_0C_00',
				'Vehicle_Opaque_Textured_NormalMapped_Emissive_AO_Livery': 'FA_D0_03_00',
				'DriveableSurface_RetroreflectivePaint_Lightmap_LineFade_rotatedUV_02': 'FB_2E_0C_00',
				'Blit2d_AutomaticExposureMeter': 'FB_72_03_00',
				'FlaptGenericShader': 'FE_27_00_00',
				'Vehicle_Greyscale_Textured_Normalmapped': 'FE_D0_03_00',
				'World_Diffuse_Specular_FlashingNeon_Singlesided': 'FF_0E_05_00'}
	
	# Adding custom shaders
	try:
		shaders.update(custom_shaders_hp())
	except:
		print("WARNING: custom_shaders function not found. Custom data will not be available.")
	
	try:
		mShaderId = shaders[shader_description]
	except:
		mShaderId = ""
		try:
			from difflib import get_close_matches
			shader_description_ = shader_description
			close_shaders = get_close_matches(shader_description.replace("NFS13",""), shaders.keys())
			for i in range(0, len(close_shaders)):
				if resource_type == "InstanceList":
					if not close_shaders[i].startswith("Vehicle"):
						shader_description = close_shaders[i]
						mShaderId = shaders[shader_description]
						print("WARNING: getting similar shader type for shader %s: %s" % (shader_description_, shader_description))
						break
				elif resource_type == "CharacterSpec":
					if close_shaders[i].startswith("Character"):
						shader_description = close_shaders[i]
						mShaderId = shaders[shader_description]
						print("WARNING: getting similar shader type for shader %s: %s" % (shader_description_, shader_description))
						break
				else:
					if close_shaders[i].startswith("Vehicle"):
						shader_description = close_shaders[i]
						mShaderId = shaders[shader_description]
						print("WARNING: getting similar shader type for shader %s: %s" % (shader_description_, shader_description))
						break
		except:
			mShaderId = ""
		if mShaderId == "":
			if resource_type == "InstanceList":
				shader_description = 'World_Diffuse_Specular_Singlesided'
				mShaderId = shaders[shader_description]
			elif resource_type == "GraphicsSpec":
				shader_description = 'Vehicle_Opaque_PaintGloss_Textured_LightmappedLights_Wrap'
				mShaderId = shaders[shader_description]
			elif resource_type == "WheelGraphicsSpec":
				shader_description = 'Vehicle_Wheel_Opaque'
				mShaderId = shaders[shader_description]
			elif resource_type == "CharacterSpec":
				shader_description = 'Character_Opaque_Textured_NormalMap_SpecMap_Skin'
				mShaderId = shaders[shader_description]
	
	mShaderId = shaders[shader_description]
	return (mShaderId, shader_description)


def get_default_material_parameters_mw_copy(shader_type):
	status = 0
	parameters_Indices = []
	parameters_Ones = []
	parameters_NamesHash = []
	parameters_Data = []
	parameters_Names = []
	
	if shader_type.lower() == "glass" or shader_type.lower() == "glass_black":	#A9_EF_09_00
		parameters_Indices = [1, 2, 5, 6, 7, 3, 8, 4, 0]
		parameters_Ones = [1, 1, 1, 1, 1, 1, 1, 1, 1]
		parameters_NamesHash = [42301036, 422585019, 529556121, 1441692693, 1444230008, 1989249925, 2342768594, 2580468578, 2907884810]
		parameters_Data = [(1.0, 0.0, 0.0, 0.0),
						   (0.0010000000474974513, 0.0, 0.0, 0.0),
						   (0.0, 0.0, 0.0, 0.0),
						   (0.16200000047683716, 0.0, 0.0, 0.0),
						   (0.12770847976207733, 0.12770847976207733, 0.12770847976207733, 1.0),
						   (0.09000000357627869, 0.0, 0.0, 0.0),
						   (1.0, 5.0, 1.0, 0.0),
						   (0.009721217676997185, 0.009134058840572834, 0.00802319310605526, 0.8767699003219604),
						   (0.0, 0.0, 0.0, 0.0)]
		parameters_Names = ['FresnelFactor', 'MaterialShadowMapBias', 'PbrMaterialDustColour', 'SurfaceSoftness', 'mCrackedGlassSpecularColour', 'OpacityMin', 'mCrackedGlassSpecularControls', 'PbrMaterialDirtColour', 'DebugOverride_GlassVolumeColour']
	
	elif shader_type == "VehicleNFS13_Glass_Textured_Lightmap":	#A7_EF_09_00
		parameters_Indices = [1, 2, 5, 10, 7, 8, 3, 9, 4, 0, 6]
		parameters_Ones = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
		parameters_NamesHash = [42301036, 422585019, 529556121, 843472246, 1441692693, 1444230008, 1989249925, 2342768594, 2580468578, 2907884810, 3743314456]
		parameters_Data = [(0.0, 0.0, 0.0, 0.0),
						   (0.0010000000474974513, 0.0, 0.0, 0.0),
						   (0.16826939582824707, 0.1384316086769104, 0.109461709856987, 0.6017727255821228),
						   (4.3460001945495605, 0.0, 0.0, 0.0),
						   (0.41499999165534973, 0.0, 0.0, 0.0),
						   (0.12770847976207733, 0.12770847976207733, 0.12770847976207733, 1.0),
						   (0.2840000092983246, 0.0, 0.0, 0.0),
						   (1.0, 5.0, 1.0, 0.0),
						   (0.009134058840572834, 0.009134058840572834, 0.009134058840572834, 0.5998314619064331),
						   (0.0060069505125284195, 0.0060069505125284195, 0.0060069505125284195, 0.049707602709531784),
						   (9.978223533835262e-05, 0.00012177028111182153, 0.000244140625, 1.0)]
		parameters_Names = ['FresnelFactor', 'MaterialShadowMapBias', 'PbrMaterialDustColour', 'mSelfIlluminationMultiplier', 'SurfaceSoftness', 'mCrackedGlassSpecularColour', 'OpacityMin', 'mCrackedGlassSpecularControls', 'PbrMaterialDirtColour', 'DebugOverride_GlassVolumeColour', 'RunningColour']
	
	elif shader_type.lower() == "mirror" or shader_type == "VehicleNFS13_Mirror":	#A9_EF_09_00
		parameters_Indices = [1, 2, 5, 6, 7, 3, 8, 4, 0]
		parameters_Ones = [1, 1, 1, 1, 1, 1, 1, 1, 1]
		parameters_NamesHash = [42301036, 422585019, 529556121, 1441692693, 1444230008, 1989249925, 2342768594, 2580468578, 2907884810]
		parameters_Data = [(1.0, 0.0, 0.0, 0.0),
						   (0.0010000000474974513, 0.0, 0.0, 0.0),
						   (0.041999999433755875, 0.03500000014901161, 0.028999999165534973, 0.25),
						   (0.5080000162124634, 0.0, 0.0, 0.0),
						   (0.11443537473678589, 0.1946178376674652, 0.21223075687885284, 1.0),
						   (0.35600000619888306, 0.0, 0.0, 0.0),
						   (0.10999999940395355, 3.5, 1.0, 0.0),
						   (0.20000000298023224, 0.20000000298023224, 0.20000000298023224, 0.10999999940395355),
						   (0.00016276036330964416, 0.00020345063239801675, 0.000244140625, 1.0)]
		parameters_Names = ['FresnelFactor', 'MaterialShadowMapBias', 'PbrMaterialDustColour', 'SurfaceSoftness', 'mCrackedGlassSpecularColour', 'OpacityMin', 'mCrackedGlassSpecularControls', 'PbrMaterialDirtColour', 'DebugOverride_GlassVolumeColour']	
	
	elif shader_type.lower() == "chrome" or shader_type == "VehicleNFS13_Chrome" or shader_type == "VehicleNFS13_Body_Chrome":	#92_EF_09_00
		parameters_Indices = [2, 4, 5, 6, 3, 1, 0]
		parameters_Ones = [1, 1, 1, 1, 1, 1, 1]
		parameters_NamesHash = [108602291, 825258624, 1236639422, 1491944071, 2428116513, 3057425025, 3447747285]
		parameters_Data = [(0.8784313797950745, 0.8784313797950745, 0.8784313797950745, 1.0),
						   (0.18000000715255737, 0.18000000715255737, 0.18000000715255737, 1.0),
						   (0.699999988079071, 0.30000001192092896, 0.0, 0.0),
						   (0.18000000715255737, 0.18000000715255737, 0.18000000715255737, 1.0),
						   (0.20000000298023224, 0.0, 0.0, 0.0),
						   (1.0, 0.0, 0.0, 0.0),
						   (1.0, 0.0, 0.0, 0.0)]
		parameters_Names = ['PbrMaterialDiffuseColour', 'PbrMaterialScuffColour', 'PbrMaterialScuffSettings', 'PbrMaterialSpecularColour', 'PbrMaterialRoughness', 'PbrMaterialClearcoatSpecular', 'PbrMaterialClearcoatFresnel']
	
	elif shader_type.lower() == "tyre" or shader_type == "VehicleNFS13_Tyre" or shader_type == "VehicleNFS13_Body_Tyre":	#9B_EF_09_00
		parameters_Indices = [3, 0, 2, 1]
		parameters_Ones = [1, 1, 1, 1]
		parameters_NamesHash = [843472246, 2143891951, 3057425025, 3447747285]
		parameters_Data = [(0.27049779891967773, 0.24228112399578094, 0.21223075687885284, 0.047659896314144135),
						   (0.0, 0.0, 0.0, 0.0),
						   (0.00039999998989515007, 0.0, 0.0, 0.0),
						   (0.0, 0.0, 0.0, 0.0)]
		parameters_Names = ['mSelfIlluminationMultiplier', 'LightmappedLightsGreenChannelColour', 'PbrMaterialClearcoatSpecular', 'PbrMaterialClearcoatFresnel']
	
	elif shader_type.lower() == "license_plate_number" or shader_type.lower() == "licenseplate_number" or shader_type == "VehicleNFS13_Licenseplate_Number" or shader_type == "VehicleNFS13_License_Plate_Number":	#9C_D4_10_00
		parameters_Indices = [4, 7, 5, 6, 0, 3, 2, 1]
		parameters_Ones = [1, 1, 1, 1, 1, 1, 1, 1]
		parameters_NamesHash = [825258624, 843472246, 1236639422, 1491944071, 2143891951, 2428116513, 3057425025, 3447747285]
		parameters_Data = [(0.18000000715255737, 0.18000000715255737, 0.18000000715255737, 1.0),
						   (1.0, 0.0, 0.0, 0.0),
						   (0.699999988079071, 0.30000001192092896, 0.0, 0.0),
						   (0.18000000715255737, 0.18000000715255737, 0.18000000715255737, 1.0),
						   (0.12583260238170624, 0.12583260238170624, 0.12583260238170624, 1.0),
						   (0.20000000298023224, 0.0, 0.0, 0.0),
						   (0.00039999998989515007, 0.0, 0.0, 0.0),
						   (0.0, 0.0, 0.0, 0.0)]
		parameters_Names = ['PbrMaterialScuffColour', 'mSelfIlluminationMultiplier', 'PbrMaterialScuffSettings', 'PbrMaterialSpecularColour', 'LightmappedLightsGreenChannelColour', 'PbrMaterialRoughness', 'PbrMaterialClearcoatSpecular', 'PbrMaterialClearcoatFresnel']
	
	elif shader_type.lower() == "license_plate" or shader_type.lower() == "licenseplate" or shader_type == "VehicleNFS13_Licenseplate" or shader_type == "VehicleNFS13_License_Plate":	#7E_EF_09_00
		parameters_Indices = [4, 7, 5, 6, 0, 3, 2, 1]
		parameters_Ones = [1, 1, 1, 1, 1, 1, 1, 1]
		parameters_NamesHash = [825258624, 843472246, 1236639422, 1491944071, 2143891951, 2428116513, 3057425025, 3447747285]
		parameters_Data = [(0.18000000715255737, 0.18000000715255737, 0.18000000715255737, 1.0),
						   (1.0, 0.0, 0.0, 0.0),
						   (0.699999988079071, 0.30000001192092896, 0.0, 0.0),
						   (0.18000000715255737, 0.18000000715255737, 0.18000000715255737, 1.0),
						   (0.12583260238170624, 0.12583260238170624, 0.12583260238170624, 1.0),
						   (0.20000000298023224, 0.0, 0.0, 0.0),
						   (0.00039999998989515007, 0.0, 0.0, 0.0),
						   (0.0, 0.0, 0.0, 0.0)]
		parameters_Names = ['PbrMaterialScuffColour', 'mSelfIlluminationMultiplier', 'PbrMaterialScuffSettings', 'PbrMaterialSpecularColour', 'LightmappedLightsGreenChannelColour', 'PbrMaterialRoughness', 'PbrMaterialClearcoatSpecular', 'PbrMaterialClearcoatFresnel']
	
	elif shader_type.lower() == "dullplastic" or shader_type.lower() == "dull_plastic":	#92_EF_09_00
		parameters_Indices = [2, 4, 5, 6, 3, 1, 0]
		parameters_Ones = [1, 1, 1, 1, 1, 1, 1]
		parameters_NamesHash = [108602291, 825258624, 1236639422, 1491944071, 2428116513, 3057425025, 3447747285]
		parameters_Data = [(0.07227185368537903, 0.07227185368537903, 0.07227185368537903, 1.0),
						   (0.18000000715255737, 0.18000000715255737, 0.18000000715255737, 1.0),
						   (0.699999988079071, 0.30000001192092896, 0.0, 0.0),
						   (0.05683362856507301, 0.0625, 0.05683362856507301, 1.0),
						   (0.5180000066757202, 0.0, 0.0, 0.0),
						   (0.0, 0.0, 0.0, 0.0),
						   (0.014000000432133675, 0.0, 0.0, 0.0)]
		parameters_Names = ['PbrMaterialDiffuseColour', 'PbrMaterialScuffColour', 'PbrMaterialScuffSettings', 'PbrMaterialSpecularColour', 'PbrMaterialRoughness', 'PbrMaterialClearcoatSpecular', 'PbrMaterialClearcoatFresnel']	
	
	elif shader_type.lower() == "interior" or shader_type == "VehicleNFS13_Interior":	#9B_EF_09_00
		parameters_Indices = [3, 0, 2, 1]
		parameters_Ones = [1, 1, 1, 1]
		parameters_NamesHash = [843472246, 2143891951, 3057425025, 3447747285]
		parameters_Data = [(1.0, 0.0, 0.0, 0.0),
						   (0.0, 0.0, 0.0, 1.0),
						   (0.00039999998989515007, 0.0, 0.0, 0.0),
						   (0.004276574589312077, 0.0, 0.0, 0.0)]
		parameters_Names = ['mSelfIlluminationMultiplier', 'LightmappedLightsGreenChannelColour', 'PbrMaterialClearcoatSpecular', 'PbrMaterialClearcoatFresnel']
	
	elif shader_type.lower() == "caliper" or shader_type.lower() == "caliper_textured" or shader_type == "VehicleNFS13_Caliper":	#B5_EF_09_00
		parameters_Indices = [4, 3, 2, 1, 0]
		parameters_Ones = [1, 1, 1, 1, 1]
		parameters_NamesHash = [529556121, 2580468578, 3057425025, 3447747285, 3998419168]
		parameters_Data = [(0.041999999433755875, 0.03500000014901161, 0.028999999165534973, 0.25),
						   (0.20000000298023224, 0.20000000298023224, 0.20000000298023224, 0.10999999940395355),
						   (0.052860647439956665, 0.0, 0.0, 0.0),
						   (0.2622506618499756, 0.0, 0.0030352699104696512, 1.0),
						   (0.0, 0.0, 0.0, 0.0)]
		parameters_Names = ['PbrMaterialDustColour', 'PbrMaterialDirtColour', 'PbrMaterialClearcoatSpecular', 'PbrMaterialClearcoatFresnel', 'g_flipUvsOnFlippedTechnique']
	
	elif shader_type.lower() == "brakedisc" or shader_type == "VehicleNFS13_BrakeDisc":    #B5_EF_09_00
		parameters_Indices = [4, 3, 2, 1, 0]
		parameters_Ones = [1, 1, 1, 1, 1]
		parameters_NamesHash = [529556121, 2580468578, 3057425025, 3447747285, 3998419168]
		parameters_Data = [(0.041999999433755875, 0.03500000014901161, 0.028999999165534973, 0.25),
						   (0.20000000298023224, 0.20000000298023224, 0.20000000298023224, 0.10999999940395355),
						   (0.015208514407277107, 0.0, 0.0, 0.0),
						   (0.03099999949336052, 0.0, 0.0, 0.0),
						   (0.0, 0.0, 0.0, 0.0)]
		parameters_Names = ['PbrMaterialDustColour', 'PbrMaterialDirtColour', 'PbrMaterialClearcoatSpecular', 'PbrMaterialClearcoatFresnel', 'g_flipUvsOnFlippedTechnique']
	
	elif shader_type.lower() == "chassis" or shader_type == "VehicleNFS13_Chassis":	#78_EF_09_00
		parameters_Indices = [1, 0]
		parameters_Ones = [1, 1]
		parameters_NamesHash = [3057425025, 3447747285]
		parameters_Data = [(0.00039999998989515007, 0.0, 0.0, 0.0),
						   (0.01856684684753418, 0.0, 0.0, 0.0)]
		parameters_Names = ['PbrMaterialClearcoatSpecular', 'PbrMaterialClearcoatFresnel']
	
	elif shader_type.lower() == "carbonfiber" or shader_type == "VehicleNFS13_Carbonfiber":	#78_EF_09_00
		parameters_Indices = [1, 0]
		parameters_Ones = [1, 1]
		parameters_NamesHash = [3057425025, 3447747285]
		parameters_Data = [(0.011612244881689548, 0.0, 0.0, 0.0),
						   (0.0, 0.0, 0.0, 0.0)]
		parameters_Names = ['PbrMaterialClearcoatSpecular', 'PbrMaterialClearcoatFresnel']
	
	elif shader_type.lower() == "carbonfiber2":	#78_EF_09_00
		parameters_Indices = [1, 0]
		parameters_Ones = [1, 1]
		parameters_NamesHash = [3057425025, 3447747285]
		parameters_Data = [(0.00039999998989515007, 0.0, 0.0, 0.0),
						   (1.0, 0.0, 0.0, 0.0)]
		parameters_Names = ['PbrMaterialClearcoatSpecular', 'PbrMaterialClearcoatFresnel']
	
	elif shader_type.lower() == "tyrenew":
		parameters_Indices = [4, 3, 2, 1, 0]
		parameters_Ones = [1, 1, 1, 1, 1]
		parameters_NamesHash = [529556121, 2580468578, 3057425025, 3447747285, 3998419168]
		parameters_Data = [(0.07227185368537903, 0.061246052384376526, 0.05126945674419403, 0.899183452129364),
						   (0.27049779891967773, 0.24228112399578094, 0.21223075687885284, 0.047659896314144135),
						   (0.00039999998989515007, 0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 0.0),
						   (0.0, 0.0, 0.0, 0.0)]
		parameters_Names = ['PbrMaterialDustColour', 'PbrMaterialDirtColour', 'PbrMaterialClearcoatSpecular', 'PbrMaterialClearcoatFresnel', 'g_flipUvsOnFlippedTechnique']
	
	elif shader_type.lower() == "tire_test":
		parameters_Indices = [3, 2, 1, 0, 4]
		parameters_Ones = [1, 1, 1, 1, 1]
		parameters_NamesHash = [529556121, 2580468578, 3057425025, 3447747285, 3998419168]
		parameters_Data = [(0.07227185368537903, 0.061246052384376526, 0.05126945674419403, 0.899183452129364),
						   (0.27049779891967773, 0.24228112399578094, 0.21223075687885284, 0.047659896314144135),
						   (0.00039999998989515007, 0.0, 0.0, 0.0),
						   (0.0, 0.0, 0.0, 0.0),
						   (0.0, 0.0, 0.0, 0.0)]
		parameters_Names = ['PbrMaterialDustColour', 'PbrMaterialDirtColour', 'PbrMaterialClearcoatSpecular', 'PbrMaterialClearcoatFresnel', 'g_flipUvsOnFlippedTechnique']
	
	else:
		status = 1
	
	return (status, [parameters_Indices, parameters_Ones, parameters_NamesHash, parameters_Data, parameters_Names])


def get_default_material_parameters_hp_copy(shader_type):
	status = 0
	parameters_Indices = []
	parameters_Ones = []
	parameters_NamesHash = []
	parameters_Data = []
	parameters_Names = []
	
	if shader_type.lower() == "glass" or shader_type.lower() == "window" or shader_type.lower() == "windows":
		#shader_type = Vehicle_Glass_Emissive_Coloured_Singlesided_Wrap
		parameters_Indices = [1, 2, 9, 4, 5, 6, 0, 8, 3, 7]
		parameters_Ones = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
		parameters_NamesHash = [422585019, 549131089, 843472246, 1350180620, 1444230008, 2342768594, 3143708811, 3681973827, 3743314456, 4272862365]
		parameters_Data = [(0.0010000000474974513, 0.0, 0.0, 0.0), (1.0, 1.0, 1.0, 1.0), (1.0, 0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0), (0.19599999487400055, 0.6549999713897705, 0.7879999876022339, 1.0), (0.10999999940395355, 3.5, 1.0, 0.0), (0.25, 0.0, 0.0, 1.0), (0.05000000074505806, 0.4000000059604645, 3.0, 0.25), (0.07035999745130539, 0.07035999745130539, 0.07035999745130539, 1.0), (0.0003035269910469651, 0.0027317428030073643, 0.0036765073891729116, 1.0)]
		parameters_Names = ['MaterialShadowMapBias', 'ReversingColour', 'mSelfIlluminationMultiplier', 'UnusedColour', 'mCrackedGlassSpecularColour', 'mCrackedGlassSpecularControls', 'BrakeColour', 'mGlassControls', 'RunningColour', 'mGlassColour']
	
	elif shader_type.lower() == "glass_black":
		#shader_type = Vehicle_Glass_Emissive_Coloured_Singlesided_Wrap
		parameters_Indices = [1, 2, 9, 4, 5, 6, 0, 8, 3, 7]
		parameters_Ones = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
		parameters_NamesHash = [422585019, 549131089, 843472246, 1350180620, 1444230008, 2342768594, 3143708811, 3681973827, 3743314456, 4272862365]
		parameters_Data = [(0.0010000000474974513, 0.0, 0.0, 0.0), (1.0, 1.0, 1.0, 1.0), (1.0, 0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0), (0.19599999487400055, 0.6549999713897705, 0.7879999876022339, 1.0), (0.10999999940395355, 3.5, 1.0, 0.0), (0.25, 0.0, 0.0, 1.0), (0.05000000074505806, 0.4000000059604645, 3.5, 0.0), (0.07035999745130539, 0.07035999745130539, 0.07035999745130539, 1.0), (0.0, 0.0, 0.0, 1.0)]
		parameters_Names = ['MaterialShadowMapBias', 'ReversingColour', 'mSelfIlluminationMultiplier', 'UnusedColour', 'mCrackedGlassSpecularColour', 'mCrackedGlassSpecularControls', 'BrakeColour', 'mGlassControls', 'RunningColour', 'mGlassColour']
	
	elif shader_type.lower() == "glass_doublesided":
		#shader_type = Vehicle_Glass_Emissive_Coloured_Wrap
		parameters_Indices = [1, 2, 9, 4, 5, 6, 0, 8, 3, 7]
		parameters_Ones = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
		parameters_NamesHash = [422585019, 549131089, 843472246, 1350180620, 1444230008, 2342768594, 3143708811, 3681973827, 3743314456, 4272862365]
		parameters_Data = [(0.0010000000474974513, 0.0, 0.0, 0.0), (1.0, 1.0, 1.0, 1.0), (1.0, 0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0), (0.19599999487400055, 0.6549999713897705, 0.7879999876022339, 1.0), (0.10999999940395355, 3.5, 1.0, 0.0), (0.25, 0.0, 0.0, 1.0), (0.03999999910593033, 1.0, 3.0, 0.699999988079071), (0.07035999745130539, 0.07035999745130539, 0.07035999745130539, 1.0), (0.0, 0.0, 0.0, 1.0)]
		parameters_Names = ['MaterialShadowMapBias', 'ReversingColour', 'mSelfIlluminationMultiplier', 'UnusedColour', 'mCrackedGlassSpecularColour', 'mCrackedGlassSpecularControls', 'BrakeColour', 'mGlassControls', 'RunningColour', 'mGlassColour']
	
	elif shader_type.lower() == "mirror" or shader_type == "VehicleNFS13_Mirror":
		#shader_type = Vehicle_Opaque_Reflective
		parameters_Indices = [1, 0, 2, 3, 4]
		parameters_Ones = [1, 1, 1, 1, 1]
		parameters_NamesHash = [422585019, 1055962784, 1738324391, 1798261942, 4142038186]
		parameters_Data = [(0.0010000000474974513, 0.0, 0.0, 0.0), (1.0, 1.0, 0.0, 0.0), (1.0, 1.0, 3.0, 0.0), (0.05000000074505806, 0.10000000149011612, 4.0, 0.0), (0.2015562504529953, 0.2015562504529953, 0.2015562504529953, 1.0)]
		parameters_Names = ['MaterialShadowMapBias', 'LightMultipliers', 'mReflectionControls', 'mSpecularControls', 'materialDiffuse']
	
	elif shader_type.lower() == "chrome" or shader_type == "VehicleNFS13_Chrome" or shader_type == "VehicleNFS13_Body_Chrome":
		#shader_type = Vehicle_Opaque_Emissive_Reflective_AO
		parameters_Indices = [5, 4, 7, 0, 6, 8, 2, 1, 3, 9]
		parameters_Ones = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
		parameters_NamesHash = [220664079, 422585019, 843472246, 1055962784, 1738324391, 1798261942, 2143891951, 3328281617, 4064316377, 4142038186]
		parameters_Data = [(0.0, 0.0, 0.0, 0.0), (0.0010000000474974513, 0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0), (1.0, 1.0, 1.0, 0.0), (0.20000000298023224, 0.44999998807907104, 5.0, 0.0), (7.0, 0.0, 30.0, 0.0), (1.0, 1.0, 1.0, 1.0), (1.0, 1.0, 1.0, 1.0), (1.0, 0.0, 0.0, 1.0), (0.00802319310605526, 0.00802319310605526, 0.00802319310605526, 1.0)]
		parameters_Names = ['mEmissiveAdditiveAmount', 'MaterialShadowMapBias', 'mSelfIlluminationMultiplier', 'LightMultipliers', 'mReflectionControls', 'mSpecularControls', 'LightmappedLightsGreenChannelColour', 'LightmappedLightsBlueChannelColour', 'LightmappedLightsRedChannelColour', 'materialDiffuse']
	
	elif shader_type.lower() == "metal":
		#shader_type = Vehicle_Opaque_Emissive_Reflective_AO
		parameters_Indices = [5, 4, 7, 0, 6, 8, 2, 1, 3, 9]
		parameters_Ones = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
		parameters_NamesHash = [220664079, 422585019, 843472246, 1055962784, 1738324391, 1798261942, 2143891951, 3328281617, 4064316377, 4142038186]
		parameters_Data = [(0.0, 0.0, 0.0, 0.0), (0.0010000000474974513, 0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0), (1.0, 1.0, 1.0, 0.0), (0.20000000298023224, 0.44999998807907104, 5.0, 0.0), (7.0, 0.0, 30.0, 0.0), (1.0, 1.0, 1.0, 1.0), (1.0, 1.0, 1.0, 1.0), (1.0, 0.0, 0.0, 1.0), (0.00802319310605526, 0.00802319310605526, 0.00802319310605526, 1.0)]
		parameters_Names = ['mEmissiveAdditiveAmount', 'MaterialShadowMapBias', 'mSelfIlluminationMultiplier', 'LightMultipliers', 'mReflectionControls', 'mSpecularControls', 'LightmappedLightsGreenChannelColour', 'LightmappedLightsBlueChannelColour', 'LightmappedLightsRedChannelColour', 'materialDiffuse']
	
	elif shader_type.lower() == "tyre" or shader_type == "VehicleNFS13_Tyre" or shader_type == "VehicleNFS13_Body_Tyre":
		#shader_type = Vehicle_Tyre
		parameters_Indices = [0, 1]
		parameters_Ones = [1, 1]
		parameters_NamesHash = [1055962784, 1798261942]
		parameters_Data = [(0.800000011920929, 0.4000000059604645, 0.0, 0.0),
						   (0.12200000137090683, 1.0, 35.0, 1.0)]
		parameters_Names = ['LightMultipliers', 'mSpecularControls']
	
	elif shader_type.lower() == "bodypaint_livery":
		#shader_type = Vehicle_Opaque_PaintGloss_Textured_LightmappedLights_Livery_Wrap
		parameters_Indices = [3, 5, 4, 1, 0, 2]
		parameters_Ones = [1, 1, 1, 1, 1, 1]
		parameters_NamesHash = [422585019, 843472246, 922074327, 2143891951, 3328281617, 4064316377]
		parameters_Data = [(0.0010000000474974513, 0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 0.0), (1.0, 0.9559733271598816, 0.68668532371521, 1.0), (1.0, 1.0, 1.0, 1.0), (1.0, 0.021219009533524513, 0.0030352699104696512, 1.0)]
		parameters_Names = ['MaterialShadowMapBias', 'mSelfIlluminationMultiplier', 'mPaintColourIndex', 'LightmappedLightsGreenChannelColour', 'LightmappedLightsBlueChannelColour', 'LightmappedLightsRedChannelColour']
	
	elif shader_type.lower() == "bodylivery":
		#shader_type = Vehicle_Opaque_PaintGloss_Textured_LightmappedLights_ColourOverride_Livery
		parameters_Indices = [10, 6, 4, 7, 14, 5, 8, 11, 0, 9, 12, 2, 1, 3, 13]
		parameters_Ones = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
		parameters_NamesHash = [83815342, 220664079, 422585019, 469755418, 536136062, 780838486, 784529858, 843472246, 1055962784, 1738324391, 1798261942, 2143891951, 3328281617, 4064316377, 4142038186]
		parameters_Data = [(0.4000000059604645, 0.15000000596046448, 50.0, 0.0), (0.0, 0.0, 0.0, 0.0), (0.0010000000474974513, 0.0, 0.0, 0.0), (0.699999988079071, 0.20000000298023224, 0.5, 0.0), (0.32314321398735046, 0.32314321398735046, 0.32314321398735046, 1.0), (2.0, 0.0, 1.0, 0.0), (2.0, 0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0), (2.0, 0.800000011920929, 1.0, 0.5), (0.03999999910593033, 0.699999988079071, 7.0, 0.0), (2.0, 0.20000000298023224, 55.0, 1.0), (0.9559733271598816, 0.9473065137863159, 1.0, 1.0), (1.0, 1.0, 1.0, 1.0), (1.0, 0.021219009533524513, 0.0030352699104696512, 1.0), (0.015208514407277107, 0.017641954123973846, 0.023153366521000862, 1.0)]
		parameters_Names = ['mScratchSpecularControls', 'mEmissiveAdditiveAmount', 'MaterialShadowMapBias', 'mEnvSpecularControls', 'pearlescentColour', 'mDiffuseFresnel', 'mPearlescentPower', 'mSelfIlluminationMultiplier', 'LightMultipliers', 'mReflectionControls', 'mSpecularControls', 'LightmappedLightsGreenChannelColour', 'LightmappedLightsBlueChannelColour', 'LightmappedLightsRedChannelColour', 'materialDiffuse']
	
	elif shader_type.lower() == "bodypaint" or shader_type.lower() == "carpaint":
		#shader_type = Vehicle_Opaque_PaintGloss_Textured_LightmappedLights_Wrap
		parameters_Indices = [3, 5, 4, 1, 0, 2]
		parameters_Ones = [1, 1, 1, 1, 1, 1]
		parameters_NamesHash = [422585019, 843472246, 922074327, 2143891951, 3328281617, 4064316377]
		parameters_Data = [(0.0010000000474974513, 0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 0.0), (1.0, 1.0, 1.0, 1.0), (1.0, 1.0, 1.0, 1.0), (1.0, 0.0, 0.0, 1.0)]
		parameters_Names = ['MaterialShadowMapBias', 'mSelfIlluminationMultiplier', 'mPaintColourIndex', 'LightmappedLightsGreenChannelColour', 'LightmappedLightsBlueChannelColour', 'LightmappedLightsRedChannelColour']
	
	elif shader_type.lower() == "bodycolor":
		#shader_type = Vehicle_Opaque_PaintGloss_Textured_LightmappedLights_ColourOverride
		parameters_Indices = [10, 6, 4, 7, 14, 5, 8, 11, 0, 9, 12, 2, 1, 3, 13]
		parameters_Ones = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
		parameters_NamesHash = [83815342, 220664079, 422585019, 469755418, 536136062, 780838486, 784529858, 843472246, 1055962784, 1738324391, 1798261942, 2143891951, 3328281617, 4064316377, 4142038186]
		parameters_Data = [(0.25, 0.25, 50.0, 0.20000000298023224), (0.0, 0.0, 0.0, 0.0), (0.0010000000474974513, 0.0, 0.0, 0.0), (0.20000000298023224, 0.20000000298023224, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0), (1.0, 0.75, 5.0, 0.0), (4.0, 0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0), (1.0, 1.0, 1.0, 0.0), (0.009999999776482582, 0.5, 3.0, 0.0), (0.05000000074505806, 0.10000000149011612, 40.0, 0.0), (1.0, 0.9386857151985168, 0.5088813304901123, 1.0), (1.0, 1.0, 1.0, 1.0), (1.0, 0.021219009533524513, 0.0030352699104696512, 1.0), (0.0036765073891729116, 0.0036765073891729116, 0.0036765073891729116, 1.0)]
		parameters_Names = ['mScratchSpecularControls', 'mEmissiveAdditiveAmount', 'MaterialShadowMapBias', 'mEnvSpecularControls', 'pearlescentColour', 'mDiffuseFresnel', 'mPearlescentPower', 'mSelfIlluminationMultiplier', 'LightMultipliers', 'mReflectionControls', 'mSpecularControls', 'LightmappedLightsGreenChannelColour', 'LightmappedLightsBlueChannelColour', 'LightmappedLightsRedChannelColour', 'materialDiffuse']
	
	elif shader_type.lower() == "badge" or shader_type.lower() == "emblem" or shader_type.lower() == "symbol" or shader_type.lower() == "transparent":
		#shader_type = Vehicle_Greyscale_Textured_Normalmapped_Reflective
		parameters_Indices = [1, 0, 2, 3, 4]
		parameters_Ones = [1, 1, 1, 1, 1]
		parameters_NamesHash = [422585019, 1055962784, 1738324391, 1798261942, 4142038186]
		parameters_Data = [(0.0010000000474974513, 0.0, 0.0, 0.0), (3.0, 1.0, 0.0, 0.0), (0.013000000268220901, 0.30000001192092896, 3.0, 0.0), (0.5, 1.0, 60.0, 1.0), (0.0, 0.0, 0.0, 1.0)]
		parameters_Names = ['MaterialShadowMapBias', 'LightMultipliers', 'mReflectionControls', 'mSpecularControls', 'materialDiffuse']
	
	elif shader_type.lower() == "grill":
		#shader_type = Vehicle_1Bit_Textured_NormalMapped_Emissive_AO_Livery
		parameters_Indices = [6, 5, 4, 7, 0, 8, 2, 1, 3, 9]
		parameters_Ones = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
		parameters_NamesHash = [83815342, 220664079, 422585019, 843472246, 1055962784, 1798261942, 2143891951, 3328281617, 4064316377, 4142038186]
		parameters_Data = [(0.009999999776482582, 0.15000000596046448, 5.0, 0.0), (0.0, 0.0, 0.0, 0.0), (0.0010000000474974513, 0.0, 0.0, 0.0), (60.0, 0.0, 0.0, 0.0), (5.0, 0.10000000149011612, 1.0, 0.0), (0.009999999776482582, 0.05000000074505806, 60.0, 0.0), (1.0, 1.0, 1.0, 1.0), (1.0, 1.0, 1.0, 1.0), (1.0, 0.0, 0.0, 1.0), (0.0, 0.0, 0.0, 1.0)]
		parameters_Names = ['mScratchSpecularControls', 'mEmissiveAdditiveAmount', 'MaterialShadowMapBias', 'mSelfIlluminationMultiplier', 'LightMultipliers', 'mSpecularControls', 'LightmappedLightsGreenChannelColour', 'LightmappedLightsBlueChannelColour', 'LightmappedLightsRedChannelColour', 'materialDiffuse']
	
	elif shader_type.lower() == "license_plate_number" or shader_type.lower() == "licenseplate_number" or shader_type == "VehicleNFS13_Licenseplate_Number" or shader_type == "VehicleNFS13_License_Plate_Number":
		#shader_type = Vehicle_Opaque_Textured_NormalMapped_Reflective_Emissive_AO_Livery
		parameters_Indices = [7, 5, 4, 8, 0, 6, 9, 2, 1, 3, 10]
		parameters_Ones = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
		parameters_NamesHash = [83815342, 220664079, 422585019, 843472246, 1055962784, 1738324391, 1798261942, 2143891951, 3328281617, 4064316377, 4142038186]
		parameters_Data = [(0.25, 0.25, 50.0, 0.10000000149011612), (0.0, 0.0, 0.0, 0.0), (0.0010000000474974513, 0.0, 0.0, 0.0), (1.5, 0.0, 0.0, 0.0), (1.0, 1.0, 1.0, 0.0), (0.009999999776482582, 0.009999999776482582, 3.0, 0.0), (0.02500000037252903, 0.800000011920929, 80.0, 1.0), (1.0, 1.0, 1.0, 1.0), (0.0, 0.0, 0.0, 1.0), (0.0, 0.0, 0.0, 1.0), (1.0, 1.0, 1.0, 1.0)]
		parameters_Names = ['mScratchSpecularControls', 'mEmissiveAdditiveAmount', 'MaterialShadowMapBias', 'mSelfIlluminationMultiplier', 'LightMultipliers', 'mReflectionControls', 'mSpecularControls', 'LightmappedLightsGreenChannelColour', 'LightmappedLightsBlueChannelColour', 'LightmappedLightsRedChannelColour', 'materialDiffuse']
	
	elif shader_type.lower() == "license_plate" or shader_type.lower() == "licenseplate" or shader_type == "VehicleNFS13_Licenseplate" or shader_type == "VehicleNFS13_License_Plate":
		#shader_type = Vehicle_Opaque_Textured_NormalMapped_Reflective_Emissive_AO_Livery
		parameters_Indices = [7, 5, 4, 8, 0, 6, 9, 2, 1, 3, 10]
		parameters_Ones = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
		parameters_NamesHash = [83815342, 220664079, 422585019, 843472246, 1055962784, 1738324391, 1798261942, 2143891951, 3328281617, 4064316377, 4142038186]
		parameters_Data = [(0.25, 0.25, 50.0, 0.10000000149011612), (0.0, 0.0, 0.0, 0.0), (0.0010000000474974513, 0.0, 0.0, 0.0), (1.5, 0.0, 0.0, 0.0), (1.0, 1.0, 1.0, 0.0), (0.009999999776482582, 0.009999999776482582, 3.0, 0.0), (0.02500000037252903, 0.800000011920929, 80.0, 1.0), (1.0, 1.0, 1.0, 1.0), (0.0, 0.0, 0.0, 1.0), (0.0, 0.0, 0.0, 1.0), (1.0, 1.0, 1.0, 1.0)]
		parameters_Names = ['mScratchSpecularControls', 'mEmissiveAdditiveAmount', 'MaterialShadowMapBias', 'mSelfIlluminationMultiplier', 'LightMultipliers', 'mReflectionControls', 'mSpecularControls', 'LightmappedLightsGreenChannelColour', 'LightmappedLightsBlueChannelColour', 'LightmappedLightsRedChannelColour', 'materialDiffuse']
	
	elif shader_type.lower() == "dullplastic" or shader_type.lower() == "dull_plastic":
		#shader_type = Vehicle_Opaque_Emissive_AO
		parameters_Indices = [5, 4, 6, 0, 7, 2, 1, 3, 8]
		parameters_Ones = [1, 1, 1, 1, 1, 1, 1, 1, 1]
		parameters_NamesHash = [220664079, 422585019, 843472246, 1055962784, 1798261942, 2143891951, 3328281617, 4064316377, 4142038186]
		parameters_Data = [(0.0, 0.0, 0.0, 0.0), (0.0010000000474974513, 0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0), (1.0, 1.0, 1.0, 0.0), (0.15000000596046448, 0.20000000298023224, 50.0, 0.6000000238418579), (1.0, 1.0, 1.0, 1.0), (1.0, 1.0, 1.0, 1.0), (1.0, 0.0, 0.0, 1.0), (0.012983032502233982, 0.012983032502233982, 0.012983032502233982, 1.0)]
		parameters_Names = ['mEmissiveAdditiveAmount', 'MaterialShadowMapBias', 'mSelfIlluminationMultiplier', 'LightMultipliers', 'mSpecularControls', 'LightmappedLightsGreenChannelColour', 'LightmappedLightsBlueChannelColour', 'LightmappedLightsRedChannelColour', 'materialDiffuse']
	
	elif shader_type.lower() == "interior" or shader_type == "VehicleNFS13_Interior":
		#shader_type = Vehicle_Opaque_Textured_Phong
		parameters_Indices = [1, 0, 2, 3]
		parameters_Ones = [1, 1, 1, 1]
		parameters_NamesHash = [422585019, 1055962784, 1798261942, 4142038186]
		parameters_Data = [(0.001500000013038516, 0.0, 0.0, 0.0), (1.0, 0.699999988079071, 0.0, 0.0), (0.05000000074505806, 0.8500000238418579, 2.0, 1.0), (1.0, 1.0, 1.0, 1.0)]
		parameters_Names = ['MaterialShadowMapBias', 'LightMultipliers', 'mSpecularControls', 'materialDiffuse']
	
	elif shader_type.lower() == "caliper" or shader_type.lower() == "caliper_textured" or shader_type == "VehicleNFS13_Caliper":
		#shader_type = Vehicle_Wheel_1Bit_Alpha_Normalmap
		parameters_Indices = [2, 4, 1, 6, 7, 5, 3, 0]
		parameters_Ones = [1, 1, 1, 1, 1, 1, 1, 1]
		parameters_NamesHash = [422585019, 780838486, 1055962784, 1738324391, 1798261942, 1967441240, 3344773910, 3998419168]
		parameters_Data = [(9.999999747378752e-06, 0.0, 0.0, 0.0), (1.0, 0.0, 5.0, 0.0), (5.0, 1.0, 0.0, 0.0), (0.0, 0.0, 30.0, 0.0), (1.0, 1.0, 60.0, 0.0), (0.012983032502233982, 0.012983032502233982, 0.012983032502233982, 1.0), (0.0, 0.0, 3.0, 0.20000000298023224), (0.0, 0.0, 0.0, 0.0)]
		parameters_Names = ['MaterialShadowMapBias', 'mDiffuseFresnel', 'LightMultipliers', 'mReflectionControls', 'mSpecularControls', 'mMaterialDiffuse', 'mBlurredReflectionControls', 'g_flipUvsOnFlippedTechnique']
	
	elif shader_type.lower() == "brakedisc" or shader_type == "VehicleNFS13_BrakeDisc":
		#shader_type = Vehicle_Wheel_Brakedisc_1Bit_Blur_Normalmap
		parameters_Indices = [2, 4, 1, 5, 6, 3, 0]
		parameters_Ones = [1, 1, 1, 1, 1, 1, 1]
		parameters_NamesHash = [422585019, 780838486, 1055962784, 1738324391, 1798261942, 3344773910, 3998419168]
		parameters_Data = [(9.999999747378752e-06, 0.0, 0.0, 0.0), (1.0, 1.0, 1.0, 0.0), (0.3499999940395355, 0.699999988079071, 1.0, 0.0), (0.0, 0.0, 0.0, 0.0), (32.0, 0.44999998807907104, 55.0, 0.0), (0.16500000655651093, 0.16500000655651093, 12.0, 0.0), (0.0, 0.0, 0.0, 0.0)]
		parameters_Names = ['MaterialShadowMapBias', 'mDiffuseFresnel', 'LightMultipliers', 'mReflectionControls', 'mSpecularControls', 'mBlurredReflectionControls', 'g_flipUvsOnFlippedTechnique']
	
	elif shader_type.lower() == "rim":
		#shader_type = Vehicle_Wheel_Opaque
		parameters_Indices = [2, 4, 1, 5, 6, 3, 0]
		parameters_Ones = [1, 1, 1, 1, 1, 1, 1]
		parameters_NamesHash = [422585019, 780838486, 1055962784, 1738324391, 1798261942, 3344773910, 3998419168]
		parameters_Data = [(9.999999747378752e-06, 0.0, 0.0, 0.0), (0.699999988079071, 1.0, 5.0, 0.0), (2.0, 1.0, 0.6000000238418579, 0.0), (0.10000000149011612, 0.30000001192092896, 5.0, 0.0), (4.0, 1.0, 15.0, 0.0), (0.10000000149011612, 0.30000001192092896, 12.0, 1.0), (0.0, 0.0, 0.0, 0.0)]
		parameters_Names = ['MaterialShadowMapBias', 'mDiffuseFresnel', 'LightMultipliers', 'mReflectionControls', 'mSpecularControls', 'mBlurredReflectionControls', 'g_flipUvsOnFlippedTechnique']
	
	elif shader_type.lower() == "rimbadge":
		#shader_type = Vehicle_Wheel_Alpha_Normalmap
		parameters_Indices = [2, 4, 1, 5, 6, 3, 0]
		parameters_Ones = [1, 1, 1, 1, 1, 1, 1]
		parameters_NamesHash = [422585019, 780838486, 1055962784, 1738324391, 1798261942, 3344773910, 3998419168]
		parameters_Data = [(9.999999747378752e-06, 0.0, 0.0, 0.0), (1.0, 1.0, 5.0, 0.0), (2.0, 0.5, 1.0, 0.0), (0.013000000268220901, 0.30000001192092896, 3.0, 0.0), (4.5, 1.0, 50.0, 0.8999999761581421), (0.6000000238418579, 0.0, 3.0, 0.20000000298023224), (1.0, 0.0, 0.0, 0.0)]
		parameters_Names = ['MaterialShadowMapBias', 'mDiffuseFresnel', 'LightMultipliers', 'mReflectionControls', 'mSpecularControls', 'mBlurredReflectionControls', 'g_flipUvsOnFlippedTechnique']
	
	elif shader_type.lower() == "chassis" or shader_type == "VehicleNFS13_Chassis":
		#shader_type = Vehicle_Opaque_Textured
		parameters_Indices = [1, 0, 2, 3]
		parameters_Ones = [1, 1, 1, 1]
		parameters_NamesHash = [422585019, 1055962784, 1798261942, 4142038186]
		parameters_Data = [(0.0010000000474974513, 0.0, 0.0, 0.0), (2.0, 0.3499999940395355, 0.0, 0.0), (0.03500000014901161, 0.25, 70.0, 1.0), (1.0, 1.0, 1.0, 1.0)]
		parameters_Names = ['MaterialShadowMapBias', 'LightMultipliers', 'mSpecularControls', 'materialDiffuse']
	
	elif shader_type.lower() == "engine":
		#shader_type = Vehicle_Opaque_Textured_Normalmapped_AO
		parameters_Indices = [1, 0, 2, 3]
		parameters_Ones = [1, 1, 1, 1]
		parameters_NamesHash = [422585019, 1055962784, 1798261942, 4142038186]
		parameters_Data = [(0.0010000000474974513, 0.0, 0.0, 0.0), (1.0, 1.0, 0.0, 0.0), (0.11999999731779099, 0.5, 20.0, 0.0), (1.0, 1.0, 1.0, 1.0)]
		parameters_Names = ['MaterialShadowMapBias', 'LightMultipliers', 'mSpecularControls', 'materialDiffuse']
	
	elif shader_type.lower() == "carbonfiber" or shader_type == "VehicleNFS13_Carbonfiber" or shader_type.lower() == "carbonfiber2":
		#shader_type = Vehicle_Opaque_PaintGloss_Textured_LightmappedLights_ColourOverride_Livery
		parameters_Indices = [10, 6, 4, 7, 14, 5, 8, 11, 0, 9, 12, 2, 1, 3, 13]
		parameters_Ones = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
		parameters_NamesHash = [83815342, 220664079, 422585019, 469755418, 536136062, 780838486, 784529858, 843472246, 1055962784, 1738324391, 1798261942, 2143891951, 3328281617, 4064316377, 4142038186]
		parameters_Data = [(0.4000000059604645, 0.15000000596046448, 50.0, 0.0), (0.0, 0.0, 0.0, 0.0), (0.0010000000474974513, 0.0, 0.0, 0.0), (0.44999998807907104, 0.20000000298023224, 0.0, 0.0), (1.0, 1.0, 1.0, 1.0), (1.5, 0.0, 4.0, 0.0), (20.0, 0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0), (1.0, 0.699999988079071, 1.0, 0.0), (0.019999999552965164, 0.4000000059604645, 12.0, 0.0), (3.0, 0.4000000059604645, 35.0, 0.9800000190734863), (0.9559733271598816, 0.9473065137863159, 1.0, 1.0), (1.0, 1.0, 1.0, 1.0), (1.0, 0.021219009533524513, 0.0030352699104696512, 1.0), (1.0, 1.0, 1.0, 1.0)]
		parameters_Names = ['mScratchSpecularControls', 'mEmissiveAdditiveAmount', 'MaterialShadowMapBias', 'mEnvSpecularControls', 'pearlescentColour', 'mDiffuseFresnel', 'mPearlescentPower', 'mSelfIlluminationMultiplier', 'LightMultipliers', 'mReflectionControls', 'mSpecularControls', 'LightmappedLightsGreenChannelColour', 'LightmappedLightsBlueChannelColour', 'LightmappedLightsRedChannelColour', 'materialDiffuse']
	
	elif shader_type.lower() == "glasscolourise" or shader_type.lower() == "glasscolour" or shader_type.lower() == "glasscolor":
		#shader_type = Vehicle_Glass_Emissive_Coloured
		parameters_Indices = [1, 2, 9, 4, 5, 6, 0, 8, 3, 7]
		parameters_Ones = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
		parameters_NamesHash = [422585019, 549131089, 843472246, 1350180620, 1444230008, 2342768594, 3143708811, 3681973827, 3743314456, 4272862365]
		parameters_Data = [(0.0010000000474974513, 0.0, 0.0, 0.0), (1.0, 1.0, 1.0, 1.0), (1.0, 0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0), (0.19599999487400055, 0.6549999713897705, 0.7879999876022339, 1.0), (0.10999999940395355, 3.5, 1.0, 0.0), (0.25, 0.0, 0.0, 1.0), (0.029999999329447746, 0.6000000238418579, 3.0, 0.949999988079071), (0.07035999745130539, 0.07035999745130539, 0.07035999745130539, 1.0), (1.0, 0.0, 0.01032982300966978, 1.0)]
		parameters_Names = ['MaterialShadowMapBias', 'ReversingColour', 'mSelfIlluminationMultiplier', 'UnusedColour', 'mCrackedGlassSpecularColour', 'mCrackedGlassSpecularControls', 'BrakeColour', 'mGlassControls', 'RunningColour', 'mGlassColour']
	
	elif shader_type.lower() == "tyrenew":
		#shader_type = Vehicle_Tyre
		parameters_Indices = [0, 1]
		parameters_Ones = [1, 1]
		parameters_NamesHash = [1055962784, 1798261942]
		parameters_Data = [(0.800000011920929, 0.4000000059604645, 0.0, 0.0),
						   (0.12200000137090683, 1.0, 35.0, 1.0)]
		parameters_Names = ['LightMultipliers', 'mSpecularControls']
		
	elif shader_type.lower() == "tire_test":
		#shader_type = Vehicle_Tyre
		parameters_Indices = [0, 1]
		parameters_Ones = [1, 1]
		parameters_NamesHash = [1055962784, 1798261942]
		parameters_Data = [(0.800000011920929, 0.4000000059604645, 0.0, 0.0),
						   (0.12200000137090683, 1.0, 35.0, 1.0)]
		parameters_Names = ['LightMultipliers', 'mSpecularControls']
	
	elif shader_type.lower() == "coplight":
		#shader_type = Vehicle_Glass_LocalEmissive_Coloured
		parameters_Indices = [0, 6, 2, 3, 7, 1, 5, 4]
		parameters_Ones = [1, 1, 1, 1, 1, 1, 1, 1]
		parameters_NamesHash = [422585019, 843472246, 1444230008, 2342768594, 2727547134, 3178546268, 3681973827, 4272862365]
		parameters_Data = [(9.999999747378752e-06, 0.0, 0.0, 0.0), (2.0, 0.0, 0.0, 0.0), (0.19599999487400055, 0.6549999713897705, 0.7879999876022339, 1.0), (0.10999999940395355, 3.5, 1.0, 0.0), (0.5, 0.0, 0.0, 0.0), (0.0666259378194809, 0.0, 0.0, 1.0), (0.009999999776482582, 1.0, 5.0, 0.5), (0.21223075687885284, 0.0006070539820939302, 0.0, 1.0)]
		parameters_Names = ['MaterialShadowMapBias', 'mSelfIlluminationMultiplier', 'mCrackedGlassSpecularColour', 'mCrackedGlassSpecularControls', 'mSelfIlluminationRadiusMultiplier', 'gEmissiveColour', 'mGlassControls', 'mGlassColour']
	
	elif shader_type.lower() == "caliperbadge":
		#shader_type = Vehicle_Wheel_1Bit_Alpha
		parameters_Indices = [2, 4, 1, 5, 6, 3, 0]
		parameters_Ones = [1, 1, 1, 1, 1, 1, 1]
		parameters_NamesHash = [422585019, 780838486, 1055962784, 1738324391, 1798261942, 3344773910, 3998419168]
		parameters_Data = [(9.999999747378752e-06, 0.0, 0.0, 0.0), (1.0, 1.0, 5.0, 0.0), (1.0, 1.0, 0.0, 0.0), (0.0, 0.0, 3.0, 0.0), (0.0, 1.0, 50.0, 0.8999999761581421), (0.0, 0.0, 3.0, 0.20000000298023224), (1.0, 0.0, 0.0, 0.0)]
		parameters_Names = ['MaterialShadowMapBias', 'mDiffuseFresnel', 'LightMultipliers', 'mReflectionControls', 'mSpecularControls', 'mBlurredReflectionControls', 'g_flipUvsOnFlippedTechnique']
	
	elif shader_type.lower() == "character" or shader_type.lower() == "driver":
		#shader_type = Character_Opaque_Textured_NormalMap_SpecMap_Skin
		parameters_Indices = [4, 3, 1, 5, 2, 0, 6]
		parameters_Ones = [1, 1, 1, 1, 1, 1, 1]
		parameters_NamesHash = [422585019, 1437161761, 1500813362, 1798261942, 2448018893, 3773525911, 4142038186]
		parameters_Data = [(0.0, 0.0, 0.0, 0.0), (2.0, 0.0, 0.0, 0.0), (0.05000000074505806, 0.0, 0.0, 0.0), (0.25, 1.0, 50.0, 0.0), (0.4000000059604645, 0.0, 0.0, 0.0), (1.2999999523162842, 0.0, 0.0, 0.0), (1.0, 1.0, 1.0, 1.0)]
		parameters_Names = ['MaterialShadowMapBias', 'KeyLightShapePower', 'FillLightBrightness', 'mSpecularControls', 'KeyLightBrightness', 'AmbientLightBrightness', 'materialDiffuse']
	
	elif shader_type.lower() == "characterskin" or shader_type.lower() == "skin":
		#shader_type = Character_Opaque_Textured_NormalMap_SpecMap_Skin
		parameters_Indices = [4, 3, 1, 5, 2, 0, 6]
		parameters_Ones = [1, 1, 1, 1, 1, 1, 1]
		parameters_NamesHash = [422585019, 1437161761, 1500813362, 1798261942, 2448018893, 3773525911, 4142038186]
		parameters_Data = [(0.0, 0.0, 0.0, 0.0), (2.5, 0.0, 0.0, 0.0), (0.09000000357627869, 0.0, 0.0, 0.0), (3.0, 1.0, 30.0, 1.0), (1.2000000476837158, 0.0, 0.0, 0.0), (1.399999976158142, 0.0, 0.0, 0.0), (0.7379103899002075, 0.7379103899002075, 0.7379103899002075, 1.0)]
		parameters_Names = ['MaterialShadowMapBias', 'KeyLightShapePower', 'FillLightBrightness', 'mSpecularControls', 'KeyLightBrightness', 'AmbientLightBrightness', 'materialDiffuse']
	
	elif shader_type.lower() == "hair":
		#shader_type = Character_Greyscale_Textured_Doublesided_Skin
		parameters_Indices = [4, 3, 1, 2, 0, 5]
		parameters_Ones = [1, 1, 1, 1, 1, 1]
		parameters_NamesHash = [422585019, 1437161761, 1500813362, 2448018893, 3773525911, 4142038186]
		parameters_Data = [(0.0, 0.0, 0.0, 0.0), (2.0, 0.0, 0.0, 0.0), (0.05000000074505806, 0.0, 0.0, 0.0), (0.4000000059604645, 0.0, 0.0, 0.0), (1.2999999523162842, 0.0, 0.0, 0.0), (1.0, 1.0, 1.0, 1.0)]
		parameters_Names = ['MaterialShadowMapBias', 'KeyLightShapePower', 'FillLightBrightness', 'KeyLightBrightness', 'AmbientLightBrightness', 'materialDiffuse']
	
	else:
		status = 1
	
	return (status, [parameters_Indices, parameters_Ones, parameters_NamesHash, parameters_Data, parameters_Names])


def bp_convert_to_crc(append_type=True, append_random_int=True):
	## Definitions
	start = 0
	stop = 10000000
	
	## Imports
	if append_random_int == True:
		from random import randint
	
	## Initializations
	models = []
	renderables = []
	materials = []
	textures = []
	polygonsoups = []
	polygonsoupmeshes = []
	StaticSoundEntities_emitter = []
	StaticSoundEntities_passby = []
	WheelSpecs = []
	wheel_TagPointSpecs = []
	SensorSpecs = []
	TagPointSpecs = []
	DrivenPoints = []
	GenericTags = []
	CameraTags = []
	LightTags = []
	IKParts = []
	GlassPanes = []
	
	random_values = {}
	
	## Processing scene
	for object in bpy.data.objects:
		if object.users_collection == ():
			continue
		
		collection = object.users_collection[0]
		try:
			resource_type = collection["resource_type"]
		except:
			continue
		
		if object.type == "MESH":
			if resource_type in ("PolygonSoupList", "Collision"):
				polygonsoupmeshes.append(object)
			else:
				renderables.append(object)
		
		elif object.type == "CAMERA":
			CameraTags.append(object)
		
		elif object.type == "EMPTY":
			if resource_type in ("GraphicsSpec", "WheelGraphicsSpec", "InstanceList", "PropInstanceData", "Wheels"):
				models.append(object)
			elif resource_type in ("PolygonSoupList", "Collision"):
				polygonsoups.append(object)
			elif resource_type == "StaticSoundMap_emitter":
				StaticSoundEntities_emitter.append(object)
			elif resource_type == "StaticSoundMap_passby":
				StaticSoundEntities_passby.append(object)
			elif resource_type == "WheelSpecs":
				WheelSpecs.append(object)
			elif resource_type == "SensorSpecs":
				SensorSpecs.append(object)
			elif resource_type == "TagPointSpecs":
				TagPointSpecs.append(object)
			elif resource_type == "DrivenPoints":
				DrivenPoints.append(object)
			elif resource_type == "GenericTags":
				GenericTags.append(object)
			elif resource_type == "LightTags":
				LightTags.append(object)
			elif resource_type == "IKPart":
				IKParts.append(object)
			elif resource_type == "GlassPanes":
				GlassPanes.append(object)
		else:
			pass
	
	for object in bpy.data.images:
		textures.append(object)
	
	for object in renderables:
		mesh = object.data
		for material in mesh.materials:
			if material not in materials:
				if material == None:
					continue
				materials.append(material)
	
	## Generating CRC32
	# Model
	type = "Model"
	for object in models:
		object_name, count = parse_name(object)
		if is_valid_id(object_name) == True:
			continue
		
		if append_type == True:
			object_name = ".".join([object_name, type])
		
		if append_random_int == True:
			try:
				value = random_values[object_name]
			except:
				value = str(randint(start, stop))
				random_values[object_name] = value
			object_name = ".".join([object_name, value])
		
		object_name = calculate_resourceid(object_name)
		if count != "":
			object_name += "." + count
		
		object.name = object_name
	
	# Renderable
	type = "Renderable"
	for object in renderables:
		object_name, count = parse_name(object)
		if is_valid_id(object_name) == True:
			continue
		
		if append_type == True:
			object_name = ".".join([object_name, type])
		
		if append_random_int == True:
			try:
				value = random_values[object_name]
			except:
				value = str(randint(start, stop))
				random_values[object_name] = value
			object_name = ".".join([object_name, value])
		
		object_name = calculate_resourceid(object_name)
		if count != "":
			object_name += "." + count
		
		object.name = object_name
	
	# Texture
	type = "Texture"
	for object in textures:
		object_name, count = parse_name(object)
		if is_valid_id(object_name) == True:
			continue
		
		if append_type == True:
			object_name = ".".join([object_name, type])
		
		if append_random_int == True:
			try:
				value = random_values[object_name]
			except:
				value = str(randint(start, stop))
				random_values[object_name] = value
			object_name = ".".join([object_name, value])
		
		object_name = calculate_resourceid(object_name)
		if count != "":
			object_name += "." + count
		
		object.name = object_name
	
	# Material
	type = "Material"
	for object in materials:
		object_name, count = parse_name(object)
		object_name_0 = object_name
		if is_valid_id(object_name) == True:
			pass
		else:
			if append_type == True:
				object_name = ".".join([object_name, type])
			
			if append_random_int == True:
				try:
					value = random_values[object_name]
				except:
					value = str(randint(start, stop))
					random_values[object_name] = value
				object_name = ".".join([object_name, value])
			
			object_name = calculate_resourceid(object_name)
			if count != "":
				object_name += "." + count
			
			object.name = object_name
		
		# Not necessary
		if object.use_nodes == True:
			for node in object.node_tree.nodes:
				if node.bl_idname in ("ShaderNodeAddShader", "ShaderNodeBsdfDiffuse", "ShaderNodeEmission", "ShaderNodeBsdfGlass", "ShaderNodeBsdfGlossy", "ShaderNodeHoldout", 
									  "ShaderNodeMixShader", "ShaderNodeBsdfPrincipled", "ShaderNodeVolumePrincipled", "ShaderNodeBsdfRefraction", "ShaderNodeEeveeSpecular", 
									  "ShaderNodeSubsurfaceScattering", "ShaderNodeBsdfTranslucent", "ShaderNodeBsdfTransparent", "ShaderNodeVolumeAbsorption", 
									  "ShaderNodeVolumeScatter", "ShaderNodeBsdfAnisotropic", "ShaderNodeBsdfVelvet", "ShaderNodeBsdfToon", "ShaderNodeBsdfHair", 
									  "ShaderNodeBsdfHairPrincipled", "ShaderNodeBackground"):
					node.name = object_name
				if node.type == "TEX_IMAGE":
					raster = node.image
					if raster != None:
						texstate_name = node.label
						if is_valid_id(texstate_name) == True:
							continue
						
						if texstate_name == "":
							node_name = parse_name(node)[0]
							texstate_name = ".".join([object_name_0, node_name])
						
						if append_type == True:
							texstate_name = ".".join([texstate_name, "TextureState"])
						
						if append_random_int == True:
							try:
								value = random_values[texstate_name]
							except:
								value = str(randint(start, stop))
								random_values[texstate_name] = value
							texstate_name = ".".join([texstate_name, value])
						
						texstate_name = calculate_resourceid(texstate_name)
						
						node.label = texstate_name
	
	return {'FINISHED'}


def nfs_convert_to_crc(append_type=True, append_random_int=True):
	## Definitions
	start = 0
	stop = 10000000
	
	## Imports
	if append_random_int == True:
		from random import randint
	
	## Initializations
	models = []
	renderables = []
	materials = []
	textures = []
	polygonsoups = []
	polygonsoupmeshes = []
	effects = []
	characters = []
	lights = []
	random_values = {}
	
	## Processing scene
	for object in bpy.data.objects:
		if object.users_collection == ():
			continue
		
		collection = object.users_collection[0]
		try:
			resource_type = collection["resource_type"]
		except:
			continue
		
		if object.type == "MESH":
			if resource_type in ("PolygonSoupList", "Collision"):
				polygonsoupmeshes.append(object)
			else:
				renderables.append(object)
		
		elif object.type == "LIGHT":
			lights.append(object)
		
		elif object.type == "EMPTY":
			if resource_type in ("GraphicsSpec", "WheelGraphicsSpec", "CharacterSpec", "InstanceList", "PropInstanceList", "DynamicInstanceList", "CompoundInstanceList", "Wheels"):
				models.append(object)
			elif resource_type in ("PolygonSoupList", "Collision"):
				polygonsoups.append(object)
			elif resource_type in ("Effects", "Effect"):
				effects.append(object)
			elif resource_type in ("Character", "Driver"):
				characters.append(object)
		else:
			pass
	
	for object in bpy.data.images:
		textures.append(object)
	
	for object in renderables:
		mesh = object.data
		for material in mesh.materials:
			if material not in materials:
				if material == None:
					continue
				materials.append(material)
	
	## Generating CRC32
	# Model
	type = "Model"
	for object in models:
		object_name, count = parse_name(object)
		if is_valid_id(object_name) == True:
			continue
		
		if append_type == True:
			object_name = ".".join([object_name, type])
		
		if append_random_int == True:
			try:
				value = random_values[object_name]
			except:
				value = str(randint(start, stop))
				random_values[object_name] = value
			object_name = ".".join([object_name, value])
		
		object_name = calculate_resourceid(object_name)
		if count != "":
			object_name += "." + count
		
		object.name = object_name
	
	# Renderable
	type = "Renderable"
	for object in renderables:
		object_name, count = parse_name(object)
		if is_valid_id(object_name) == True:
			continue
		
		if append_type == True:
			object_name = ".".join([object_name, type])
		
		if append_random_int == True:
			try:
				value = random_values[object_name]
			except:
				value = str(randint(start, stop))
				random_values[object_name] = value
			object_name = ".".join([object_name, value])
		
		object_name = calculate_resourceid(object_name)
		if count != "":
			object_name += "." + count
		
		object.name = object_name
	
	# Texture
	type = "Texture"
	for object in textures:
		object_name, count = parse_name(object)
		if is_valid_id(object_name) == True:
			continue
		
		if append_type == True:
			object_name = ".".join([object_name, type])
		
		if append_random_int == True:
			try:
				value = random_values[object_name]
			except:
				value = str(randint(start, stop))
				random_values[object_name] = value
			object_name = ".".join([object_name, value])
		
		object_name = calculate_resourceid(object_name)
		if count != "":
			object_name += "." + count
		
		object.name = object_name
	
	# Material
	type = "Material"
	for object in materials:
		#object_name, count = parse_name(object)
		object_name = object.name
		count = ""
		if is_valid_id(object_name) == True:
			continue
		
		if append_type == True:
			object_name = ".".join([object_name, type])
		
		if append_random_int == True:
			try:
				value = random_values[object_name]
			except:
				value = str(randint(start, stop))
				random_values[object_name] = value
			object_name = ".".join([object_name, value])
		
		object_name = calculate_resourceid(object_name)
		if count != "":
			object_name += "." + count
		
		object.name = object_name
		
		# Not necessary
		if object.use_nodes == True:
			for node in object.node_tree.nodes:
				if node.bl_idname in ("ShaderNodeAddShader", "ShaderNodeBsdfDiffuse", "ShaderNodeEmission", "ShaderNodeBsdfGlass", "ShaderNodeBsdfGlossy", "ShaderNodeHoldout", 
									  "ShaderNodeMixShader", "ShaderNodeBsdfPrincipled", "ShaderNodeVolumePrincipled", "ShaderNodeBsdfRefraction", "ShaderNodeEeveeSpecular", 
									  "ShaderNodeSubsurfaceScattering", "ShaderNodeBsdfTranslucent", "ShaderNodeBsdfTransparent", "ShaderNodeVolumeAbsorption", 
									  "ShaderNodeVolumeScatter", "ShaderNodeBsdfAnisotropic", "ShaderNodeBsdfVelvet", "ShaderNodeBsdfToon", "ShaderNodeBsdfHair", 
									  "ShaderNodeBsdfHairPrincipled", "ShaderNodeBackground"):
					node.name = object_name
				if node.type == "TEX_IMAGE":
					raster = node.image
					if raster != None:
						node.label = raster.name
	
	return {'FINISHED'}


def create_sphere(name="dgi_sphere", radius=1.0):
	# Create an empty mesh and the object.
	me_ob = bpy.data.meshes.new(name)
	obj = bpy.data.objects.new(name, me_ob)

	# Construct the bmesh sphere and assign it to the blender mesh.
	bm = bmesh.new()
	bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=radius)
	for f in bm.faces:
		f.smooth = True
	bm.to_mesh(me_ob)
	bm.free()
	
	return obj


def parse_name(object):
	object_name = object.name
	
	splitted_str = object_name.split(".")
	count = ""
	if len(splitted_str) > 1:
		try:
			count = int(splitted_str[-1])
			count = splitted_str[-1]
		except:
			count = ""
	
		object_name = ".".join(splitted_str[:-1])
	
	return (object_name, count)


def calculate_padding(lenght, alignment):
	division1 = (lenght/alignment)
	division2 = math.ceil(lenght/alignment)
	padding = int((division2 - division1)*alignment)
	return padding


def bytes_to_id(id):
	id = binascii.hexlify(id)
	id = str(id,'ascii')
	id = id.upper()
	id = '_'.join([id[x : x+2] for x in range(0, len(id), 2)])
	return id


def int_to_id(id):
	id = str(hex(int(id)))[2:].upper().zfill(8)
	id = '_'.join([id[::-1][x : x+2][::-1] for x in range(0, len(id), 2)])
	return id


def is_valid_id(id):
	id_old = id
	id = id.replace('_', '')
	id = id.replace(' ', '')
	id = id.replace('-', '')
	if len(id) != 8:
		return False
	try:
		int(id, 16)
	except ValueError:
		return False
	
	return True


def calculate_resourceid(resource_name):
	ID = hex(zlib.crc32(resource_name.lower().encode()) & 0xffffffff)
	ID = ID[2:].upper().zfill(8)
	ID = '_'.join([ID[::-1][x:x+2][::-1] for x in range(0, len(ID), 2)])
	return ID


def vec_roll_to_mat3(vec, roll):
	#https://blender.stackexchange.com/questions/9318/set-a-bones-matrix-to-a-custom-matrix/90240#90240
	#port of the updated C function from armature.c
	#https://developer.blender.org/T39470
	#note that C accesses columns first, so all matrix indices are swapped compared to the C version
	
	nor = vec.normalized()
	THETA_THRESHOLD_NEGY = 1.0e-9
	THETA_THRESHOLD_NEGY_CLOSE = 1.0e-5
	
	#create a 3x3 matrix
	bMatrix = Matrix().to_3x3()
	
	theta = 1.0 + nor[1];
	
	if (theta > THETA_THRESHOLD_NEGY_CLOSE) or ((nor[0] or nor[2]) and theta > THETA_THRESHOLD_NEGY):

		bMatrix[1][0] = -nor[0];
		bMatrix[0][1] = nor[0];
		bMatrix[1][1] = nor[1];
		bMatrix[2][1] = nor[2];
		bMatrix[1][2] = -nor[2];
		if theta > THETA_THRESHOLD_NEGY_CLOSE:
			#If nor is far enough from -Y, apply the general case.
			bMatrix[0][0] = 1 - nor[0] * nor[0] / theta;
			bMatrix[2][2] = 1 - nor[2] * nor[2] / theta;
			bMatrix[0][2] = bMatrix[2][0] = -nor[0] * nor[2] / theta;
		
		else:
			#If nor is too close to -Y, apply the special case.
			theta = nor[0] * nor[0] + nor[2] * nor[2];
			bMatrix[0][0] = (nor[0] + nor[2]) * (nor[0] - nor[2]) / -theta;
			bMatrix[2][2] = -bMatrix[0][0];
			bMatrix[0][2] = bMatrix[2][0] = 2.0 * nor[0] * nor[2] / theta;
	
	else:
		#If nor is -Y, simple symmetry by Z axis.
		bMatrix = Matrix().to_3x3()
		bMatrix[0][0] = bMatrix[1][1] = -1.0;
	
	#Make Roll matrix
	rMatrix = Matrix.Rotation(roll, 3, nor)
	
	#Combine and output result
	mat = rMatrix * bMatrix
	return mat


def mat3_to_vec_roll(mat):
	#https://blender.stackexchange.com/questions/9318/set-a-bones-matrix-to-a-custom-matrix/90240#90240
    vec = mat.col[1]
    vecmat = vec_roll_to_mat3(mat.col[1], 0)
    vecmatinv = vecmat.inverted()
    rollmat = vecmatinv * mat
    roll = math.atan2(rollmat[0][2], rollmat[2][2])
    return vec, roll


def BurnoutLibraryGet():
	spaths = bpy.utils.script_paths()
	for rpath in spaths:
		tpath = rpath + '\\addons\\BurnoutParadise'
		if os.path.exists(tpath):
			npath = '"' + tpath + '"'
			return tpath
	return None

	
def NFSMWLibraryGet():
	spaths = bpy.utils.script_paths()
	for rpath in spaths:
		tpath = rpath + '\\addons\\NeedForSpeedMostWanted2012'
		if os.path.exists(tpath):
			npath = '"' + tpath + '"'
			return tpath
	return None


def NFSHPLibraryGet():
	spaths = bpy.utils.script_paths()
	for rpath in spaths:
		tpath = rpath + '\\addons\\NeedForSpeedHotPursuit'
		if os.path.exists(tpath):
			npath = '"' + tpath + '"'
			return tpath
	return None


"""
Main menu
"""
class MESH_MT_criterion_modding_tools(bpy.types.Menu):
	"""Add custom data"""
	bl_idname = "MESH_MT_criterion_modding_tools"
	bl_label = "Criterion modding tools"

	def draw(self, context):
		layout = self.layout
		layout.menu("MESH_MT_material_properties_submenu", icon="ADD")
		layout.menu("MESH_MT_load_effects_driver_submenu", icon="PASTEDOWN")
		layout.menu("MESH_MT_calculate_crc32_submenu", icon="RNA_ADD")
		layout.menu("MESH_MT_swap_ids_submenu", icon="RNA_ADD")
		layout.menu("MESH_MT_texture_type_identifier_submenu", icon="TEXTURE")
		layout.menu("MESH_MT_transfer_blend_data_submenu", icon="UV_SYNC_SELECT")


"""
SubMenus
"""
class MESH_MT_material_properties_submenu(bpy.types.Menu):
	"""Add material custom properties"""
	bl_idname = "MESH_MT_material_properties_submenu"
	bl_label = "Add material custom properties"

	def draw(self, context):
		layout = self.layout
		layout.operator(MESH_OT_bp_properties.bl_idname, icon="EVENT_B")
		layout.operator(MESH_OT_hp_properties.bl_idname, icon="EVENT_N")
		layout.operator(MESH_OT_mw_properties.bl_idname, icon="EVENT_N")


class MESH_MT_load_effects_driver_submenu(bpy.types.Menu):
	"""Load effects and driver data"""
	bl_idname = "MESH_MT_load_effects_driver_submenu"
	bl_label = "Load skeleton/effects/driver data"

	def draw(self, context):
		layout = self.layout
		layout.operator(MESH_OT_hp_load_effect_driver.bl_idname, icon="EVENT_N")
		layout.operator(MESH_OT_mw_load_effect_driver.bl_idname, icon="EVENT_N")


class MESH_MT_calculate_crc32_submenu(bpy.types.Menu):
	"""Generate valid resource IDs"""
	bl_idname = "MESH_MT_calculate_crc32_submenu"
	bl_label = "Generate resource IDs"

	def draw(self, context):
		layout = self.layout
		layout.operator(MESH_OT_bp_crc32.bl_idname, icon="EVENT_B")
		layout.operator(MESH_OT_nfs_crc32.bl_idname, icon="EVENT_N")


class MESH_MT_texture_type_identifier_submenu(bpy.types.Menu):
	"""Identify texture types"""
	bl_idname = "MESH_MT_texture_type_identifier_submenu"
	bl_label = "Identify texture types"

	def draw(self, context):
		layout = self.layout
		#layout.operator(MESH_OT_bp_texture_type.bl_idname, icon="EVENT_B")
		layout.operator(MESH_OT_hp_texture_type.bl_idname, icon="EVENT_N")
		layout.operator(MESH_OT_mw_texture_type.bl_idname, icon="EVENT_N")


class MESH_MT_transfer_blend_data_submenu(bpy.types.Menu):
	"""Transfer blend data"""
	bl_idname = "MESH_MT_transfer_blend_data_submenu"
	bl_label = "Transfer blend data"

	def draw(self, context):
		layout = self.layout
		layout.operator(MESH_OT_transfer_blend_data.bl_idname, icon="RIGHTARROW")


class MESH_MT_swap_ids_submenu(bpy.types.Menu):
	"""Swap the endianness of resource IDs"""
	bl_idname = "MESH_MT_swap_ids_submenu"
	bl_label = "Swap IDs endianness"

	def draw(self, context):
		layout = self.layout
		layout.operator(MESH_OT_swap_ids.bl_idname, icon="RIGHTARROW")


"""
Operators
"""
class MESH_OT_bp_properties(bpy.types.Operator):
	bl_idname = "mesh.bp_properties"
	bl_label = "Burnout Paradise"
	bl_description = "Create and populate custom properties for exporting to Burnout Paradise"
	
	def execute(self, context):
		self.report({'INFO'}, "Running add custom properties operator")
		status = main_bp()
		self.report({'INFO'}, "Finished")
		return status


class MESH_OT_mw_properties(bpy.types.Operator):
	bl_idname = "mesh.mw_properties"
	bl_label = "Need for Speed Most Wanted 2012"
	bl_description = "Create and populate custom properties for exporting to Need for Speed Most Wanted 2012"
	
	def execute(self, context):
		self.report({'INFO'}, "Running add custom properties operator")
		status = main_mw()
		self.report({'INFO'}, "Finished")
		return status


class MESH_OT_hp_properties(bpy.types.Operator):
	bl_idname = "mesh.hp_properties"
	bl_label = "Need for Speed Hot Pursuit"
	bl_description = "Create and populate custom properties for exporting to Need for Speed Hot Pursuit"
	
	def execute(self, context):
		self.report({'INFO'}, "Running add custom properties operator")
		status = main_hp()
		self.report({'INFO'}, "Finished")
		return status


@orientation_helper(axis_forward='-Y', axis_up='Z')
class MESH_OT_mw_load_effect_driver(bpy.types.Operator):
	bl_idname = "mesh.mw_load_effect_driver"
	bl_label = "Need for Speed Most Wanted 2012"
	bl_description = "Load skeleton, effects and driver data from library for exporting to Need for Speed Most Wanted 2012"
	
	
	def draw(self, context):
		layout = self.layout
		layout.use_property_split = True
		layout.use_property_decorate = False  # No animation.
		
		##
		box = layout.box()
		split = box.split(factor=0.75)
		col = split.column(align=True)
		col.label(text="Blender orientation", icon="OBJECT_DATA")
		
		row = box.row(align=True)
		row.label(text="Forward axis")
		row.use_property_split = False
		row.prop_enum(self, "axis_forward", 'X', text='X')
		row.prop_enum(self, "axis_forward", 'Y', text='Y')
		row.prop_enum(self, "axis_forward", 'Z', text='Z')
		row.prop_enum(self, "axis_forward", '-X', text='-X')
		row.prop_enum(self, "axis_forward", '-Y', text='-Y')
		row.prop_enum(self, "axis_forward", '-Z', text='-Z')
		
		row = box.row(align=True)
		row.label(text="Up axis")
		row.use_property_split = False
		row.prop_enum(self, "axis_up", 'X', text='X')
		row.prop_enum(self, "axis_up", 'Y', text='Y')
		row.prop_enum(self, "axis_up", 'Z', text='Z')
		row.prop_enum(self, "axis_up", '-X', text='-X')
		row.prop_enum(self, "axis_up", '-Y', text='-Y')
		row.prop_enum(self, "axis_up", '-Z', text='-Z')
	
	
	def invoke(self, context, event):
		wm = context.window_manager

		return wm.invoke_props_dialog(self, width=500)
	
	
	def execute(self, context):
		self.report({'INFO'}, "Running load skeleton/effects/driver data")
		
		global_matrix = axis_conversion(from_forward='Z', from_up='Y', to_forward=self.axis_forward, to_up=self.axis_up).to_4x4()
		
		status = load_vehicle_data_mw(global_matrix)
		self.report({'INFO'}, "Finished")
		return status


@orientation_helper(axis_forward='-Y', axis_up='Z')
class MESH_OT_hp_load_effect_driver(bpy.types.Operator):
	bl_idname = "mesh.hp_load_effect_driver"
	bl_label = "Need for Speed Hot Pursuit"
	bl_description = "Load skeleton, effects and driver data from library for exporting to Need for Speed Hot Pursuit"
	
	
	def draw(self, context):
		layout = self.layout
		layout.use_property_split = True
		layout.use_property_decorate = False  # No animation.
		
		##
		box = layout.box()
		split = box.split(factor=0.75)
		col = split.column(align=True)
		col.label(text="Blender orientation", icon="OBJECT_DATA")
		
		row = box.row(align=True)
		row.label(text="Forward axis")
		row.use_property_split = False
		row.prop_enum(self, "axis_forward", 'X', text='X')
		row.prop_enum(self, "axis_forward", 'Y', text='Y')
		row.prop_enum(self, "axis_forward", 'Z', text='Z')
		row.prop_enum(self, "axis_forward", '-X', text='-X')
		row.prop_enum(self, "axis_forward", '-Y', text='-Y')
		row.prop_enum(self, "axis_forward", '-Z', text='-Z')
		
		row = box.row(align=True)
		row.label(text="Up axis")
		row.use_property_split = False
		row.prop_enum(self, "axis_up", 'X', text='X')
		row.prop_enum(self, "axis_up", 'Y', text='Y')
		row.prop_enum(self, "axis_up", 'Z', text='Z')
		row.prop_enum(self, "axis_up", '-X', text='-X')
		row.prop_enum(self, "axis_up", '-Y', text='-Y')
		row.prop_enum(self, "axis_up", '-Z', text='-Z')
	
	
	def invoke(self, context, event):
		wm = context.window_manager

		return wm.invoke_props_dialog(self, width=500)
	
	
	def execute(self, context):
		self.report({'INFO'}, "Running load skeleton/effects/driver data")
		
		global_matrix = axis_conversion(from_forward='Z', from_up='Y', to_forward=self.axis_forward, to_up=self.axis_up).to_4x4()
		
		status = load_vehicle_data_hp(global_matrix)
		self.report({'INFO'}, "Finished")
		return status


class MESH_OT_bp_crc32(bpy.types.Operator):
	bl_idname = "mesh.bp_crc32"
	bl_label = "Burnout Paradise"
	bl_description = "Convert the data names to a valid resource ID"
	
	append_type: BoolProperty(
			name="Append resource type to names",
			description="Check in order to append the resource type to the object names, then calculate the resourceId. It is recommend to check this option",
			default=True,
			)
	
	append_random_int: BoolProperty(
			name="Append random number to names",
			description="Check in order to append a random number to the object names, then calculate the resourceId. It is recommend to check this option",
			default=True,
			)
	
	def draw(self, context):
		layout = self.layout
		layout.use_property_split = False
		layout.use_property_decorate = False  # No animation.
		
		##
		box = layout.box()
		split = box.split(factor=0.75)
		col = split.column(align=True)
		col.label(text="Preferences", icon="OPTIONS")
		
		box.prop(self, "append_type")
		box.prop(self, "append_random_int")
	
	
	def invoke(self, context, event):
		wm = context.window_manager

		return wm.invoke_props_dialog(self, width=200)
	
	
	def execute(self, context):
		self.report({'INFO'}, "Running ResourceId calculator operator")
		status = bp_convert_to_crc(self.append_type, self.append_random_int)
		self.report({'INFO'}, "Finished")
		return status


class MESH_OT_nfs_crc32(bpy.types.Operator):
	bl_idname = "mesh.nfs_crc32"
	bl_label = "Need for Speed HP/MW"
	bl_description = "Convert the data names to a valid resource ID"
	
	append_type: BoolProperty(
			name="Append resource type to names",
			description="Check in order to append the resource type to the object names, then calculate the resourceId. It is recommended to check this option",
			default=True,
			)
	
	append_random_int: BoolProperty(
			name="Append random number to names",
			description="Check in order to append a random number to the object names, then calculate the resourceId. It is recommended to check this option",
			default=True,
			)
	
	def draw(self, context):
		layout = self.layout
		layout.use_property_split = False
		layout.use_property_decorate = False  # No animation.
		
		##
		box = layout.box()
		split = box.split(factor=0.75)
		col = split.column(align=True)
		col.label(text="Preferences", icon="OPTIONS")
		
		box.prop(self, "append_type")
		box.prop(self, "append_random_int")
	
	
	def invoke(self, context, event):
		wm = context.window_manager

		return wm.invoke_props_dialog(self, width=200)
	
	
	def execute(self, context):
		self.report({'INFO'}, "Running ResourceId calculator operator")
		status = nfs_convert_to_crc(self.append_type, self.append_random_int)
		self.report({'INFO'}, "Finished")
		return status


class MESH_OT_swap_ids(bpy.types.Operator):
	bl_idname = "mesh.swap_ids"
	bl_label = "Burnout Paradise | Need for Speed HP/MW"
	bl_description = "Convert the endianness of the resource IDs"
	
	ignore_hidden_meshes: BoolProperty(
			name="Ignore hidden meshes",
			description="Check in order to ignore the hidden meshes in the swap IDs operations",
			default=True,
			)
	
	def draw(self, context):
		layout = self.layout
		layout.use_property_split = False
		layout.use_property_decorate = False  # No animation.
		
		##
		box = layout.box()
		split = box.split(factor=0.75)
		col = split.column(align=True)
		col.label(text="Preferences", icon="OPTIONS")
		
		box.prop(self, "ignore_hidden_meshes")
	
	
	def invoke(self, context, event):
		wm = context.window_manager

		return wm.invoke_props_dialog(self, width=200)
	
	
	def execute(self, context):
		self.report({'INFO'}, "Running swap resource IDs operator")
		status = mw_swap_ids(self.ignore_hidden_meshes)
		self.report({'INFO'}, "Finished")
		return status


class MESH_OT_mw_texture_type(bpy.types.Operator):
	bl_idname = "mesh.mw_texture_type"
	bl_label = "Need for Speed Most Wanted 2012"
	bl_description = "Identify texture types"
	
	def execute(self, context):
		self.report({'INFO'}, "Running identify texture types operator")
		
		sampler_types = ('DiffuseTextureSampler', 'SpecularTextureSampler', 'CrumpleTextureSampler', 'EffectsTextureSampler',
						 'LightmapLightsTextureSampler', 'NormalTextureSampler', 'EmissiveTextureSampler', 'ColourSampler',
						 'ExternalNormalTextureSampler', 'InternalNormalTextureSampler', 'DisplacementSampler',
						 'CrackedGlassTextureSampler', 'CrackedGlassNormalTextureSampler', 'LightmapTextureSampler',
						 'BlurNormalTextureSampler', 'BlurDiffuseTextureSampler', 'BlurEffectsTextureSampler',
						 'BlurSpecularTextureSampler', 'AmbientOcclusionTextureSampler', 'AoSpecMapTextureSampler',
						 'OverlayTextureSampler', 'ReflectionTextureSampler', 'IlluminanceTextureSampler', 'DiffuseSampler',
						 'UvDistortionSampler', 'MaskTextureSampler', 'Tiling3NormalSampler', 'DecalTextureSampler',
						 'Tiling1NormalSampler', 'Tiling3TextureSampler', 'Tiling2NormalSampler', 'Tiling2TextureSampler',
						 'Tiling1TextureSampler', 'BlendTextureSampler', 'SpecularColourTextureSampler', 'NoiseTextureSampler',
						 'ColourMap_Sampler', 'SpecColour_Sampler', 'Normal_Sampler', 'DetailMap_Normal_Sampler', 'RoadDepth_Sampler',
						 'DetailMap_Diffuse_Sampler', 'PuddleTextureSampler', 'Line_Diffuse_Sampler', 'Line_NormalPlusSpec_Sampler',
						 'AOMapTextureSampler', 'GradientRemapSampler', 'cubeSampler', 'RoadBlockTextureSampler',
						 'SpecDepthAndRefractionTextureSampler', 'SurfNormalTextureSampler', 'DiffuseAndCausticsTextureSampler',
						 'SurfTextureSampler', 'SurfMaskTextureSampler', 'RiverFloorTextureSampler', 'EdgeAlphaPlusAoMap_Sampler',
						 'EdgeNormalMap_Sampler', 'Decal_Diffuse_Sampler', 'Decal_NormalPlusSpec_Sampler', 'NeonMaskTextureSampler',
						 'NormalTexture2Sampler', 'SpecularTexture2Sampler', 'DiffuseTexture2Sampler', 'ProjectiveTextureSampler',
						 'SlipDiffuseSampler', 'SpinDiffuseSampler', 'SlipNormalSampler', 'ThermalSampler', 'RunDiffuseSampler',
						 'RunNormalSampler', 'SpinNormalSampler', 'RoughnessAOSampler', 'SpecularSampler', 'NormalSampler',
						 'cubeReflectionSampler', 'NormalAndAlphaMaskSampler')
		
		for mat in bpy.data.materials:
			if mat.node_tree == None:
				continue
			
			sampler_types_used = []
			for node in mat.node_tree.nodes:
				if node.type == "TEX_IMAGE":
					if node.name in sampler_types:
						sampler_types_used.append(node.name)
			
			for node in mat.node_tree.nodes:
				if node.type == "TEX_IMAGE":
					if node.name not in sampler_types:
						for link in node.outputs[0].links:
							if link.to_node.bl_idname == "ShaderNodeBsdfPrincipled":
								if link.to_node.inputs[:].index(link.to_socket) == 0 and "DiffuseTextureSampler" not in sampler_types_used:
									node.name = "DiffuseTextureSampler"
									sampler_types_used.append(node.name)
								elif link.to_node.inputs[:].index(link.to_socket) == 7 and "SpecularTextureSampler" not in sampler_types_used:
									node.name = "SpecularTextureSampler"
									sampler_types_used.append(node.name)
								elif link.to_node.inputs[:].index(link.to_socket) == 22 and "NormalTextureSampler" not in sampler_types_used:
									node.name = "NormalTextureSampler"
									sampler_types_used.append(node.name)
							break # ignoring other links
			
			for node in mat.node_tree.nodes:
				if node.type == "TEX_IMAGE":
					if node.name not in sampler_types:
						if len(node.outputs[0].links) == 0:
							if node.name.lower() == "diffuse" and "DiffuseTextureSampler" not in sampler_types_used:
								node.name = "DiffuseTextureSampler"
								sampler_types_used.append(node.name)
							elif node.name.lower() == "specular" and "SpecularTextureSampler" not in sampler_types_used:
								node.name = "SpecularTextureSampler"
								sampler_types_used.append(node.name)
							elif node.name.lower() == "normal" and "NormalTextureSampler" not in sampler_types_used:
								node.name = "NormalTextureSampler"
								sampler_types_used.append(node.name)
							elif node.name.lower() == "crumple" and "CrumpleTextureSampler" not in sampler_types_used:
								node.name = "CrumpleTextureSampler"
								sampler_types_used.append(node.name)
							elif node.name.lower() == "emissive" and "EmissiveTextureSampler" not in sampler_types_used:
								node.name = "EmissiveTextureSampler"
								sampler_types_used.append(node.name)
							elif node.name.lower() == "ao" and "AmbientOcclusionTextureSampler" not in sampler_types_used:
								node.name = "AmbientOcclusionTextureSampler"
								sampler_types_used.append(node.name)
		
		status = {'FINISHED'}
		
		self.report({'INFO'}, "Finished")
		return status


class MESH_OT_hp_texture_type(bpy.types.Operator):
	bl_idname = "mesh.hp_texture_type"
	bl_label = "Need for Speed Hot Pursuit"
	bl_description = "Identify texture types"
	
	def execute(self, context):
		self.report({'INFO'}, "Running identify texture types operator")
		
		sampler_types = ('NormalTextureSampler', 'DiffuseTextureSampler', 'OverlayTextureSampler', 'DiffuseSampler', 'ReflectionTextureSampler',
						 'OffsetTextureSampler', 'IlluminanceTextureSampler', 'Diffuse2TextureSampler', 'NormalSampler', 'OverlayB_Sampler',
						 'OverlayA_Sampler', 'ColourMap_Sampler', 'Crack_Normal_Sampler', 'DetailMap_Normal_Sampler', 'Crack_AO_Sampler',
						 'DetailMap_Diffuse_Sampler', 'NoiseSampler', 'SpecularTextureSampler', 'MaskTextureSampler', 'Tiling3NormalSampler',
						 'Tiling1NormalSampler', 'CliffMaskAndLightingTextureSampler', 'Tiling3TextureSampler', 'Tiling2NormalSampler',
						 'RGBOverlayTextureSampler', 'NoiseTextureSampler', 'Tiling2TextureSampler', 'Tiling1TextureSampler', 'CliffNormalSampler',
						 'CliffTextureSampler', 'dirtMapSampler', 'detailDiffuseMapSampler', 'detailNormalMapSampler', 'AOMapSampler',
						 'crackNormalMapSampler', 'WindowTintSampler', 'DecalTextureSampler', 'TyreMarkTextureSampler', 'EdgeNormalMap_Sampler',
						 'EdgeAlphaPlusAoMap_Sampler', 'Decal_Diffuse_Sampler', 'Decal_NormalPlusSpec_Sampler', 'Line_Diffuse_Sampler',
						 'Line_NormalPlusSpec_Sampler', 'IllumTextureSampler', 'RoadBlockTextureSampler', 'SpecDepthAndRefractionTextureSampler',
						 'SurfNormalTextureSampler', 'DiffuseAndCausticsTextureSampler', 'SurfTextureSampler', 'SurfMaskTextureSampler',
						 'RiverFloorTextureSampler', 'NormalSpecTextureSampler', 'ProjectiveTextureSampler', 'NeonMaskTextureSampler')
		
		for mat in bpy.data.materials:
			if mat.node_tree == None:
				continue
			
			sampler_types_used = []
			for node in mat.node_tree.nodes:
				if node.type == "TEX_IMAGE":
					if node.name in sampler_types:
						sampler_types_used.append(node.name)
			
			for node in mat.node_tree.nodes:
				if node.type == "TEX_IMAGE":
					if node.name not in sampler_types:
						for link in node.outputs[0].links:
							if link.to_node.bl_idname == "ShaderNodeBsdfPrincipled":
								if link.to_node.inputs[:].index(link.to_socket) == 0 and "DiffuseTextureSampler" not in sampler_types_used:
									node.name = "DiffuseTextureSampler"
									sampler_types_used.append(node.name)
								elif link.to_node.inputs[:].index(link.to_socket) == 7 and "SpecularTextureSampler" not in sampler_types_used:
									node.name = "SpecularTextureSampler"
									sampler_types_used.append(node.name)
								elif link.to_node.inputs[:].index(link.to_socket) == 22 and "NormalTextureSampler" not in sampler_types_used:
									node.name = "NormalTextureSampler"
									sampler_types_used.append(node.name)
							break # ignoring other links
			
			for node in mat.node_tree.nodes:
				if node.type == "TEX_IMAGE":
					if node.name not in sampler_types:
						if len(node.outputs[0].links) == 0:
							if node.name.lower() == "diffuse" and "DiffuseTextureSampler" not in sampler_types_used:
								node.name = "DiffuseTextureSampler"
								sampler_types_used.append(node.name)
							elif node.name.lower() == "specular" and "SpecularTextureSampler" not in sampler_types_used:
								node.name = "SpecularTextureSampler"
								sampler_types_used.append(node.name)
							elif node.name.lower() == "normal" and "NormalTextureSampler" not in sampler_types_used:
								node.name = "NormalTextureSampler"
								sampler_types_used.append(node.name)
							elif node.name.lower() == "crumple" and "CrumpleTextureSampler" not in sampler_types_used:
								node.name = "CrumpleTextureSampler"
								sampler_types_used.append(node.name)
							elif node.name.lower() == "emissive" and "EmissiveTextureSampler" not in sampler_types_used:
								node.name = "EmissiveTextureSampler"
								sampler_types_used.append(node.name)
							elif node.name.lower() == "ao" and "AmbientOcclusionTextureSampler" not in sampler_types_used:
								node.name = "AmbientOcclusionTextureSampler"
								sampler_types_used.append(node.name)
		
		status = {'FINISHED'}
		
		self.report({'INFO'}, "Finished")
		return status


def get_collections(scene, context):
		items = []
		for i, collection in enumerate(bpy.data.collections):
			items.append(('OPT_%d' % i, collection.name, collection.name))
		
		return tuple(items)


class MESH_OT_transfer_blend_data(bpy.types.Operator):
	bl_idname = "mesh.transfer_blend_data"
	bl_label = "Burnout Paradise | Need for Speed HP/MW"
	bl_description = "Transfer blend indices and weight data from source objects to target objects"
	
	
	src_collection: EnumProperty(
			name="Source collection",
			description="Choose the collection with the source objects",
			items=get_collections,
			)
	
	tgt_collection: EnumProperty(
			name="Target collection",
			description="Choose the collection with the target objects",
			items=get_collections,
			)
	
	ignore_src_hidden_meshes: BoolProperty(
			name="Ignore source hidden meshes",
			description="Check in order to ignore the hidden meshes of the source collection",
			default=True,
			)
	
	ignore_tgt_hidden_meshes: BoolProperty(
			name="Ignore target hidden meshes",
			description="Check in order to ignore the hidden meshes of the target collection",
			default=True,
			)

	@classmethod 
	def poll(cls, context):
		return bpy.context.scene != None

	def draw(self, context):
		layout = self.layout
		layout.use_property_split = False
		layout.use_property_decorate = False  # No animation.
		
		##
		box = layout.box()
		split = box.split(factor=0.75)
		col = split.column(align=True)
		col.label(text="Settings", icon="SETTINGS")
		
		box.prop(self, "src_collection")
		box.prop(self, "tgt_collection")
		
		box.prop(self, "ignore_src_hidden_meshes")
		box.prop(self, "ignore_tgt_hidden_meshes")


	def invoke(self, context, event):
		wm = context.window_manager
		
		return wm.invoke_props_dialog(self, width=400)


	def execute(self, context):
		self.report({'INFO'}, "Running transfer blend data operator")
		
		
		def closest_node(node, nodes):
			nodes = np.asarray(nodes)
			deltas = nodes - node
			dist_2 = np.einsum('ij,ij->i', deltas, deltas)
			return np.argmin(dist_2)
		
		
		#os.system('cls')
		#start_time = time.time()
		
		## Getting source and target collection names
		items_callback = self.__annotations__.get("src_collection").keywords.get("items")
		items = items_callback(self, context)
		
		src_collection_name = next(item[1] for item in items if item[0] == self.src_collection)
		tgt_collection_name = next(item[1] for item in items if item[0] == self.tgt_collection)
		
		## Getting source and target objects
		src_objects = []
		tgt_objects = []
		
		for object in bpy.data.collections[src_collection_name].objects:
			if object.type != "MESH":
				continue
			if object.hide_get() == True and self.ignore_src_hidden_meshes == True:
				continue
			src_objects.append(object)
		
		for object in bpy.data.collections[tgt_collection_name].objects:
			if object.type != "MESH":
				continue
			if object.hide_get() == True  and self.ignore_tgt_hidden_meshes == True:
				continue
			tgt_objects.append(object)
		
		## Getting data
		bm = bmesh.new()
		src_coordinates = []
		blends_indices = []
		blends_weights = []
		for src_object in src_objects:
			src_mesh = src_object.data
			
			bm.from_mesh(src_mesh)
			
			blend_index1 = (bm.verts.layers.int.get("blend_index1") or bm.verts.layers.int.new('blend_index1'))
			blend_index2 = (bm.verts.layers.int.get("blend_index2") or bm.verts.layers.int.new('blend_index2'))
			blend_index3 = (bm.verts.layers.int.get("blend_index3") or bm.verts.layers.int.new('blend_index3'))
			blend_index4 = (bm.verts.layers.int.get("blend_index4") or bm.verts.layers.int.new('blend_index4'))
			
			blend_weight1 = (bm.verts.layers.float.get("blend_weight1") or bm.verts.layers.float.new('blend_weight1'))
			blend_weight2 = (bm.verts.layers.float.get("blend_weight2") or bm.verts.layers.float.new('blend_weight2'))
			blend_weight3 = (bm.verts.layers.float.get("blend_weight3") or bm.verts.layers.float.new('blend_weight3'))
			blend_weight4 = (bm.verts.layers.float.get("blend_weight4") or bm.verts.layers.float.new('blend_weight4'))
			
			src_matrix = src_object.matrix_world
			
			for vert in bm.verts:
				vert_co = src_matrix @ vert.co
				src_coordinates.append(vert_co)
				
				blends_indices.append([vert[blend_index1], vert[blend_index2], vert[blend_index3], vert[blend_index4]])
				blends_weights.append([vert[blend_weight1], vert[blend_weight2], vert[blend_weight3], vert[blend_weight4]])
			
			bm.clear()
		
		src_coordinates = np.asarray(src_coordinates)
		
		for tgt_object in tgt_objects:
			tgt_mesh = tgt_object.data
			
			bm.from_mesh(tgt_mesh)
			
			blend_index1 = (bm.verts.layers.int.get("blend_index1") or bm.verts.layers.int.new('blend_index1'))
			blend_index2 = (bm.verts.layers.int.get("blend_index2") or bm.verts.layers.int.new('blend_index2'))
			blend_index3 = (bm.verts.layers.int.get("blend_index3") or bm.verts.layers.int.new('blend_index3'))
			blend_index4 = (bm.verts.layers.int.get("blend_index4") or bm.verts.layers.int.new('blend_index4'))
			
			blend_weight1 = (bm.verts.layers.float.get("blend_weight1") or bm.verts.layers.float.new('blend_weight1'))
			blend_weight2 = (bm.verts.layers.float.get("blend_weight2") or bm.verts.layers.float.new('blend_weight2'))
			blend_weight3 = (bm.verts.layers.float.get("blend_weight3") or bm.verts.layers.float.new('blend_weight3'))
			blend_weight4 = (bm.verts.layers.float.get("blend_weight4") or bm.verts.layers.float.new('blend_weight4'))
			
			tgt_matrix = tgt_object.matrix_world
			
			for vert in bm.verts:
				idx = closest_node(tgt_matrix @ vert.co, src_coordinates)
				vert[blend_index1] = blends_indices[idx][0]
				vert[blend_index2] = blends_indices[idx][1]
				vert[blend_index3] = blends_indices[idx][2]
				vert[blend_index4] = blends_indices[idx][3]

				vert[blend_weight1] = blends_weights[idx][0]
				vert[blend_weight2] = blends_weights[idx][1]
				vert[blend_weight3] = blends_weights[idx][2]
				vert[blend_weight4] = blends_weights[idx][3]
			
			bm.to_mesh(tgt_mesh)
			bm.clear()
		
		bm.free()
		
		#elapsed_time = time.time() - start_time
		#print("Elapsed time: %.4fs" % elapsed_time)
		
		status = {'FINISHED'}
		
		self.report({'INFO'}, "Finished")
		return status


def mw_swap_ids(ignore_hidden_meshes):
	## Initializations
	models = []
	renderables = []
	materials = []
	textures = []
	polygonsoups = []
	polygonsoupmeshes = []
	effects = []
	characters = []
	lights = []
	
	## Processing scene
	for object in bpy.data.objects:
		if object.users_collection == ():
			continue
		
		if object.hide_get() == True and ignore_hidden_meshes == True:
			continue
		
		collection = object.users_collection[0]
		try:
			resource_type = collection["resource_type"]
		except:
			continue
		
		if object.type == "MESH":
			if resource_type in ("PolygonSoupList", "Collision"):
				polygonsoupmeshes.append(object)
			else:
				renderables.append(object)
		
		elif object.type == "LIGHT":
			lights.append(object)
		
		elif object.type == "EMPTY":
			if resource_type in ("GraphicsSpec", "WheelGraphicsSpec", "InstanceList", "PropInstanceList", "DynamicInstanceList", "CompoundInstanceList", "Wheels"):
				models.append(object)
			elif resource_type in ("PolygonSoupList", "Collision"):
				polygonsoups.append(object)
			elif resource_type in ("Effects", "Effect"):
				effects.append(object)
			elif resource_type in ("Character", "Driver"):
				characters.append(object)
		else:
			pass
	
	for object in bpy.data.images:
		textures.append(object)
	
	for object in renderables:
		mesh = object.data
		for material in mesh.materials:
			if material not in materials:
				materials.append(material)
	
	## Swapping endianness
	# Model
	for object in models:
		object_name, count = parse_name(object)
		if is_valid_id(object_name) == True:
			pass
		else:
			#object_name = calculate_resourceid(object_name)
			continue
		
		object_name = swap_resource_id(object_name)
		
		if count != "":
			object_name += "." + count
		
		object.name = object_name
	
	# Renderable
	type = "Renderable"
	for object in renderables:
		object_name, count = parse_name(object)
		if is_valid_id(object_name) == True:
			pass
		else:
			#object_name = calculate_resourceid(object_name)
			continue
		
		object_name = swap_resource_id(object_name)
		
		if count != "":
			object_name += "." + count
		
		object.name = object_name
	
	# Texture
	type = "Texture"
	for object in textures:
		object_name, count = parse_name(object)
		if is_valid_id(object_name) == True:
			pass
		else:
			#object_name = calculate_resourceid(object_name)
			continue
		
		object_name = swap_resource_id(object_name)
		
		if count != "":
			object_name += "." + count
		
		object.name = object_name
	
	# Material
	type = "Material"
	for object in materials:
		object_name, count = parse_name(object)
		if is_valid_id(object_name) == True:
			pass
		else:
			#object_name = calculate_resourceid(object_name)
			continue
		
		object_name = swap_resource_id(object_name)
		
		if count != "":
			object_name += "." + count
		
		object.name = object_name
		
		# Not necessary
		if object.use_nodes == True:
			for node in object.node_tree.nodes:
				if node.bl_idname in ("ShaderNodeAddShader", "ShaderNodeBsdfDiffuse", "ShaderNodeEmission", "ShaderNodeBsdfGlass", "ShaderNodeBsdfGlossy", "ShaderNodeHoldout", 
									  "ShaderNodeMixShader", "ShaderNodeBsdfPrincipled", "ShaderNodeVolumePrincipled", "ShaderNodeBsdfRefraction", "ShaderNodeEeveeSpecular", 
									  "ShaderNodeSubsurfaceScattering", "ShaderNodeBsdfTranslucent", "ShaderNodeBsdfTransparent", "ShaderNodeVolumeAbsorption", 
									  "ShaderNodeVolumeScatter", "ShaderNodeBsdfAnisotropic", "ShaderNodeBsdfVelvet", "ShaderNodeBsdfToon", "ShaderNodeBsdfHair", 
									  "ShaderNodeBsdfHairPrincipled", "ShaderNodeBackground"):
					node.name = object_name
				if node.type == "TEX_IMAGE":
					raster = node.image
					if raster != None:
						node.label = raster.name
	
	return {'FINISHED'}


def swap_resource_id(mResourceId):
	mResourceId = mResourceId.replace('_', '')
	mResourceId = mResourceId[::-1]
	mResourceId = '_'.join([mResourceId[x:x+2][::-1] for x in range(0, len(mResourceId), 2)])
	return mResourceId


def menu_func(self, context):
	self.layout.separator()
	self.layout.menu(MESH_MT_criterion_modding_tools.bl_idname, icon="AUTO")


register_classes = (
		MESH_MT_criterion_modding_tools,
		MESH_MT_material_properties_submenu,
		MESH_MT_load_effects_driver_submenu,
		MESH_MT_calculate_crc32_submenu,
		MESH_MT_swap_ids_submenu,
		MESH_MT_texture_type_identifier_submenu,
		MESH_MT_transfer_blend_data_submenu,
		MESH_OT_bp_properties,
		MESH_OT_mw_properties,
		MESH_OT_hp_properties,
		MESH_OT_mw_load_effect_driver,
		MESH_OT_hp_load_effect_driver,
		MESH_OT_bp_crc32,
		MESH_OT_nfs_crc32,
		MESH_OT_swap_ids,
		MESH_OT_mw_texture_type,
		MESH_OT_hp_texture_type,
		MESH_OT_transfer_blend_data,
)


def register():
	for cls in register_classes:
		bpy.utils.register_class(cls)
	bpy.types.VIEW3D_MT_add.append(menu_func)


def unregister():
	for cls in register_classes:
		bpy.utils.unregister_class(cls)
	bpy.types.VIEW3D_MT_add.remove(menu_func)
