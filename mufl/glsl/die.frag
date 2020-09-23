#version 330

out vec4 f_color;
in vec2 uv;
in float norm_z;
uniform sampler2D tex;

void main() {
    f_color = texture(tex, uv);
}
