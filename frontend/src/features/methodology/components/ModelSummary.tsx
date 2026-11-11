import { ErrorState } from '@/components/ui/ErrorState'
import { LoadingState } from '@/components/ui/LoadingState'
import { useModelMetrics } from '@/features/methodology/hooks/useMethodology'
import { formatShare } from '@/utils/format'

interface Scored {
  name?: string
  test_mape?: number
  validation_mape?: number
}

/** Home-value model results and site-score weights, read from the model_runs table. */
export function ModelSummary() {
  const { data, isPending, isError, error } = useModelMetrics()
  if (isPending) return <LoadingState label="Loading model results" />
  if (isError) return <ErrorState error={error} />
  const hv = data.home_value?.metrics as
    | { baseline?: Scored; chosen_model?: Scored; test_improvement_vs_baseline?: number; target_met?: boolean }
    | undefined
  const weights = (data.site_scoring?.params.weights ?? {}) as Record<string, number>
  const desc = (data.site_scoring?.params.descriptions ?? {}) as Record<string, string>
  return (
    <div className="grid gap-6 md:grid-cols-2">
      <section>
        <h3 className="font-semibold">Home-value model (land and home cost context)</h3>
        {hv ? (
          <dl className="mt-2 text-sm">
            <div className="flex justify-between border-b border-rule/60 py-1">
              <dt>Baseline (town median), test error</dt>
              <dd className="tabular-nums">{formatShare(hv.baseline?.test_mape)}</dd>
            </div>
            <div className="flex justify-between border-b border-rule/60 py-1">
              <dt>Chosen model ({hv.chosen_model?.name}), test error</dt>
              <dd className="tabular-nums">{formatShare(hv.chosen_model?.test_mape)}</dd>
            </div>
            <div className="flex justify-between border-b border-rule/60 py-1">
              <dt>Improvement over baseline (target 25%)</dt>
              <dd className="tabular-nums">
                {formatShare(hv.test_improvement_vs_baseline)}, target {hv.target_met ? 'met' : 'not met'}
              </dd>
            </div>
          </dl>
        ) : (
          <p className="text-ink-soft">No model run recorded.</p>
        )}
        <p className="mt-2 text-xs text-ink-soft">
          Error is the mean absolute percentage error on a test split used once, after the model
          was chosen on a separate validation split.
        </p>
      </section>
      <section>
        <h3 className="font-semibold">Site score weights</h3>
        <ul className="mt-2 space-y-1 text-sm">
          {Object.entries(weights)
            .sort((a, b) => b[1] - a[1])
            .map(([k, w]) => (
            <li key={k} className="flex justify-between gap-3 border-b border-rule/60 py-1">
              <span>{desc[k] ?? k}</span>
              <span className="tabular-nums">{formatShare(w)}</span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}
