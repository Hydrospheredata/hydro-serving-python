import hydro_serving_grpc as hs


def add(a, b):
    val_a = a.int_val[0]
    val_b = b.int_val[0]

    return hs.PredictResponse(
        outputs={
            "sum": hs.TensorProto(dtype=hs.DT_INT8, tensor_shape=hs.TensorShapeProto(), int_val=[val_a + val_b])
        }
    )
