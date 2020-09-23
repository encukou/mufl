#version 330

out vec4 f_color;
in vec2 uv;
in vec4 color;
in float norm_z;
uniform sampler2D tex;

void main() {
    if (norm_z > 0) discard;
    f_color = color * texture(tex, uv);
}
