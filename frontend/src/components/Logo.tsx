// export function Logo() {
//   return (
//     <div className="flex items-center space-x-2">
//       <img 
//         src="src/components/logo/23-Brainlabs-Secondary-Logo-Horizontal-1.png" 
//         alt="brainlabs" 
//         className="h-8"
//       />
//       <div className="h-8 w-px bg-gray-300" />
//       <img 
//         src="src/components/logo/Thermo1.png" 
//         alt="Thermo Scientific" 
//         className="h-8"
//       />
//     </div>
//   )
// } 


import ThermoLogo from '@/components/logo/Thermo1.png';
import BrainlabsLogo from '@/components/logo/23-Brainlabs-Secondary-Logo-Horizontal-1.png';

export function Logo() {
  return (
    <div className="flex items-center space-x-2">
      <img src={BrainlabsLogo} alt="brainlabs" className="h-8" />
      <div className="h-8 w-px bg-gray-300" />
      <img src={ThermoLogo} alt="Thermo Scientific" className="h-8" />
    </div>
  );
}
