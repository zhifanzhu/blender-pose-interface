import bpy
import numpy as np


def create_point_cloud(verts: np.array, 
                       point_size: float = 0.01,
                       colors: np.array = None,
                       name='PointCloud', 
                       collection_name='Collection'):
    """
    Args:
        point_size: (N, 3), in meters
        colors: (N, 4), 0-1 RGBA values for each point
    """
    pcd_mesh = bpy.data.meshes.new(name)  # add the new mesh
    pcd_obj = bpy.data.objects.new(pcd_mesh.name, pcd_mesh)
    collect = bpy.data.collections[collection_name]
    collect.objects.link(pcd_obj)
    bpy.context.view_layer.objects.active = pcd_obj  # This sets the active object (?)

    pcd_mesh.from_pydata(verts, edges=[], faces=[])

    # Add material
    material = bpy.data.materials.new('PointCloud Material')
    pcd_obj.data.materials.append(material)

    modifier = pcd_obj.modifiers.new("Mesh-to-Point Modifier", "NODES")
    # Link back to the modifier
    modifier.node_group = create_mesh_to_points_group(material=material, point_size=point_size)  

    if colors is not None:
        assert len(verts) == len(colors), f"Length of verts and colors must be the same. Got {len(verts)} and {len(colors)}"
        assert colors.shape[1] == 4, f"Colors must have 4 channels. Got {colors.shape[1]}"
        # Add 'Col' attribute for color
        Col = pcd_obj.data.attributes.new(name="Col", type='FLOAT_COLOR', domain='POINT')
        for i, c in enumerate(colors):
            Col.data[i].color = c
        # Add ShaderNode 
        # For full list of nodes, see
        #  https://blender.stackexchange.com/questions/257936/is-there-an-easy-way-to-import-point-clouds-with-colors-in-blender-3-2
        material.use_nodes = True  # This creates a new node_tree
        attribute_node = material.node_tree.nodes.new(type='ShaderNodeAttribute')
        attribute_node.attribute_name = 'Col'
        attribute_node.location = (-200, 0)
        material.node_tree.links.new(attribute_node.outputs[0], material.node_tree.nodes['Material Output'].inputs[0])

    return pcd_mesh


def create_mesh_to_points_group(material: bpy.types.Material,
                                name="Mesh to Points Group",
                                point_size=0.01):
    """ The goal of this is to be able to control the point-size in the point-cloud.

    Access the `group` in blender via: bpy.context.object.modifiers[0].node_group,
        or bpy.data.node_groups['Mesh to Points Group']

    See 'Geometry Nodes' in GUI for output.
    """
    group = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    group.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    input_node = group.nodes.new('NodeGroupInput')
    input_node.select = False
    input_node.location.x = -200 - input_node.width

    mesh_to_point_node = group.nodes.new(type='GeometryNodeMeshToPoints')
    mesh_to_point_node.select = False
    mesh_to_point_node.location.x = 0
    # mesh_to_point_node.inputs[3].default_value = point_size  # '3' is the point size field

    set_point_radius_node = group.nodes.new(type='GeometryNodeSetPointRadius')
    set_point_radius_node.select = False
    set_point_radius_node.location.x = 200
    set_point_radius_node.inputs[2].default_value = point_size  # '2' is the radius size field

    set_material_node = group.nodes.new(type='GeometryNodeSetMaterial')
    set_material_node.select = False
    set_material_node.location.x = 400
    set_material_node.inputs[2].default_value = material

    group.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    output_node = group.nodes.new('NodeGroupOutput')
    output_node.is_active_output = True
    output_node.select = False
    output_node.location.x = 600

    group.links.new(input_node.outputs[0], mesh_to_point_node.inputs[0])
    group.links.new(mesh_to_point_node.outputs[0], set_point_radius_node.inputs[0])
    group.links.new(set_point_radius_node.outputs[0], set_material_node.inputs[0])
    group.links.new(set_material_node.outputs[0], output_node.inputs[0])
    group.is_modifier = True
    return group


def create_video_to_camera(mp4_path: str,
                           Camera: bpy.types.Object,
                           frame_duration: int,
                           name='RefVideo'):
    """ Add a reference Video as a child of the Camera
    """
    Camera_topleft, _, _, _ = Camera.data.view_frame()
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = 'IMAGE'
    empty.empty_display_size = 1.0  # Default
    ref_video = bpy.data.images.load(mp4_path, check_existing=True)
    ref_video.colorspace_settings.name = 'Non-Color'
    empty.data = ref_video
    empty.image_user.frame_duration = frame_duration
    empty.image_user.frame_start = 0
    empty.image_user.frame_offset = 0

    empty.use_empty_image_alpha = True
    empty.color[3] = 0.60  # Set Transparency

    empty.location = (0, 0, Camera_topleft[2])
    empty.parent = Camera
    bpy.context.collection.objects.link(empty)
    return empty
