const std = @import("std");

const FType = f64;

const srgb_gamma: FType = 2.4;
const srgb_inv_gamma: FType = 1.0 / srgb_gamma;
const gamma_threshold: FType = 0.0031308;
const inv_gamma_threshold: FType = 0.04045;
const gamma_a: FType = 0.055;
const gamma_b: FType = 1.055;
const scale: FType = 12.92;

fn linear_to_srgb(x: FType) FType {
    if (x >= gamma_threshold) {
        return gamma_b * std.math.pow(FType, x, srgb_inv_gamma) - gamma_a;
    } else {
        return scale * x;
    }
}

fn srgb_to_linear(x: FType) FType {
    if (x >= inv_gamma_threshold) {
        return std.math.pow(FType, (x + gamma_a) / gamma_b, srgb_gamma);
    } else {
        return x / scale;
    }
}

const Lab = @Vector(3, FType);
const RGB = @Vector(3, FType);
const Lms = @Vector(3, FType);

fn cbrt(x: FType) FType {
    return std.math.pow(FType, x, 1.0 / 3.0);
}

fn linear_srgb_to_oklab(c: RGB) Lab {
    const lms = Lms{
        0.4122214708 * c[0] + 0.5363325363 * c[1] + 0.0514459929 * c[2],
        0.2119034982 * c[0] + 0.6806995451 * c[1] + 0.1073969566 * c[2],
        0.0883024619 * c[0] + 0.2817188376 * c[1] + 0.6299787005 * c[2],
    };

    const lms_ = Lms{
        cbrt(lms[0]),
        cbrt(lms[1]),
        cbrt(lms[2]),
    };

    return Lab{
        0.2104542553 * lms_[0] + 0.7936177850 * lms_[1] - 0.0040720468 * lms_[2],
        1.9779984951 * lms_[0] - 2.4285922050 * lms_[1] + 0.4505937099 * lms_[2],
        0.0259040371 * lms_[0] + 0.7827717662 * lms_[1] - 0.8086757660 * lms_[2],
    };
}

fn oklab_to_linear_srgb(c: Lab) RGB {
    const lms_ = Lms{
        c[0] + 0.3963377774 * c[1] + 0.2158037573 * c[2],
        c[0] - 0.1055613458 * c[1] - 0.0638541728 * c[2],
        c[0] - 0.0894841775 * c[1] - 1.2914855480 * c[2],
    };

    const lms = Lms{
        lms_[0] * lms_[0] * lms_[0],
        lms_[1] * lms_[1] * lms_[1],
        lms_[2] * lms_[2] * lms_[2],
    };

    return RGB{
        4.0767416621 * lms[0] - 3.3077115913 * lms[1] + 0.2309699292 * lms[2],
        -1.2684380046 * lms[0] + 2.6097574011 * lms[1] - 0.3413193965 * lms[2],
        -0.0041960863 * lms[0] - 0.7034186147 * lms[1] + 1.7076147010 * lms[2],
    };
}

fn srgb_to_oklab(c: RGB) Lab {
    const linear = RGB{ srgb_to_linear(c[0]), srgb_to_linear(c[1]), srgb_to_linear(c[2]) };
    return linear_srgb_to_oklab(linear);
}

fn oklab_to_srgb(c: Lab) RGB {
    const linear = oklab_to_linear_srgb(c);
    return RGB{ linear_to_srgb(linear[0]), linear_to_srgb(linear[1]), linear_to_srgb(linear[2]) };
}

pub fn main() !void {
    var allocator = std.heap.ArenaAllocator.init(std.heap.page_allocator);
    defer allocator.deinit();
    const alloc = allocator.allocator();

    var args = try std.process.argsAlloc(alloc);
    defer std.process.argsFree(alloc, args);

    const stdout = std.io.getStdOut().writer();
    const stderr = std.io.getStdErr().writer();

    if (args.len != 4 and args.len != 5) {
        const name = if (args.len >= 1) args[0] else "oklab";
        try stderr.print(
            \\Usage:
            \\    {s} [convert] RED GREEN BLUE
            \\    {s} reverse L A B
            \\
        , .{ name, name });
        return std.process.exit(1);
    }

    const colourSlice = args[args.len - 3 ..];
    if (args.len == 5 and std.mem.eql(u8, args[1], "reverse")) {
        // Convert OKLAB to SRGB
        const l = try std.fmt.parseFloat(FType, colourSlice[0]);
        const a = try std.fmt.parseFloat(FType, colourSlice[1]);
        const b = try std.fmt.parseFloat(FType, colourSlice[2]);

        const c = Lab{ l, a, b };
        const rgb = oklab_to_srgb(c);

        try stdout.print("vec3({d:.8}, {d:.8}, {d:.8})\n", .{ rgb[0], rgb[1], rgb[2] });
    } else if (args.len == 5 and !std.mem.eql(u8, args[1], "convert")) {
        try stderr.print("Unknown command: {s}\n", .{args[1]});
        return std.process.exit(1);
    } else {
        // Convert SRGB to OKLAB
        const red = try std.fmt.parseFloat(FType, colourSlice[0]);
        const green = try std.fmt.parseFloat(FType, colourSlice[1]);
        const blue = try std.fmt.parseFloat(FType, colourSlice[2]);

        const c = RGB{ red, green, blue };
        const lab = srgb_to_oklab(c);

        try stdout.print("vec3({d:.8}, {d:.8}, {d:.8})\n", .{ lab[0], lab[1], lab[2] });
    }

    std.process.cleanExit();
}
