"""Example set for duel.json: a floor, two walls and a pillar. `pw.py duel` runs this file inside Blender and then
calls build(). A room script only builds geometry (no render); it can read the duel file as DUEL, and may make a
camera object for the duel file to name ({"camera": {"object": "..."}})."""
import bmesh
import bpy


def block(name, size, at):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    bmesh.ops.translate(bm, vec=at, verts=bm.verts)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    bpy.context.scene.collection.objects.link(bpy.data.objects.new(name, me))


def build():
    block("floor", (14, 14, 0.1), (1, 0, -0.05))
    block("back_wall", (0.3, 14, 4), (6, 0, 2))
    block("side_wall", (14, 0.3, 4), (1, 5, 2))
    block("pillar", (0.6, 0.6, 4), (3.6, -2.4, 2))
