#include <assert.h>

#include "coco.h"
#include "coco_problem.c"

typedef struct {
  double factor;
} _puv_data_t;

static void _puv_evaluate_function(coco_problem_t *self, const double *x, double *y) {
	_puv_data_t *data = coco_get_transform_data(self);
	const double *lower_bounds = self->smallest_values_of_interest;
	const double *upper_bounds = self->largest_values_of_interest;
	double penalty = 0.0;
	size_t i;
	for (i = 0; i < self->number_of_variables; ++i) {
		const double c1 = x[i] - upper_bounds[i];
		const double c2 = lower_bounds[i] - x[i];
		assert(lower_bounds[i] < upper_bounds[i]);
		if (c1 > 0.0) {
			penalty += c1 * c1;
		} else if (c2 > 0.0) {
			penalty += c2 * c2;
		}
	}
	assert(coco_get_transform_inner_problem(self) != NULL);
	/*assert(problem->state != NULL);*/
	coco_evaluate_function(coco_get_transform_inner_problem(self), x, y);
	for (i = 0; i < self->number_of_objectives; ++i) {
		y[i] += data->factor * penalty;
	}
}

/**
 * penalize_uninteresting_values(inner_problem):
 *
 * Add a penalty to all evaluations outside of the region of interest
 * of ${inner_problem}.
 */
static coco_problem_t *penalize_uninteresting_values(coco_problem_t *inner_problem, const double factor) {
	coco_problem_t *self;
	_puv_data_t *data;
	assert(inner_problem != NULL);
	/* assert(offset != NULL); */
	
	data = coco_allocate_memory(sizeof(*data));
	data->factor = factor;
	self = coco_allocate_transformed_problem(inner_problem, data, NULL);
	self->evaluate_function = _puv_evaluate_function;
	return self;
}